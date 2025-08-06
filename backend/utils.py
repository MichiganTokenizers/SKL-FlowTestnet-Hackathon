import math
import sqlite3
from typing import Any, List # Added List for type hinting
import logging

# This file can be used for other utility functions if needed in the future. 

def get_escalated_contract_costs(draft_amount: float, duration: int, contract_start_year: int) -> list[dict[str, Any]]:
    """
    Calculates the escalated cost for each year of a contract.

    Args:
        draft_amount (float): The initial auction cost for Year 1.
        duration (int): The length of the contract in years.
        contract_start_year (int): The season year the contract starts.

    Returns:
        list[dict[str, Any]]: A list of dictionaries, where each dictionary
                              has 'year' (int) and 'cost' (float).
    """
    costs_by_year = []
    current_cost = draft_amount
    for i in range(duration):
        year = contract_start_year + i
        costs_by_year.append({'year': year, 'cost': current_cost})
        # For subsequent years, escalate by 10% of the current year's cost, rounded up
        if i < duration - 1: # No need to calculate next year's cost if it's the last year
            current_cost = math.ceil(current_cost * 1.1)
    return costs_by_year

def apply_contract_penalties_and_deactivate(
    contract_row_id: int, 
    draft_amount: float, 
    contract_duration: int, 
    contract_start_year: int, 
    year_dropped: int, 
    is_currently_offseason_when_dropped: bool, # New parameter
    db_conn: sqlite3.Connection, 
    logger: logging.Logger
):
    if not logger:
        logger = logging.getLogger(__name__)
        logger.warning("apply_contract_penalties_and_deactivate: Logger not provided, using default.")

    cursor = db_conn.cursor()
    try:
        contract_start_year = int(contract_start_year)
        year_dropped = int(year_dropped)
        contract_duration = int(contract_duration)

        # Determine the first calendar year a penalty will actually be applied against a team's cap
        if is_currently_offseason_when_dropped:
            first_actual_penalty_hit_year = year_dropped
        else:
            first_actual_penalty_hit_year = year_dropped + 1
        
        logger.info(f"Penalty calc for contract {contract_row_id}: Dropped in {year_dropped} (is_offseason={is_currently_offseason_when_dropped}). First penalty hit year: {first_actual_penalty_hit_year}")

        # Number of penalty installments is based on remaining years from the drop point in the contract
        # Example: 3yr contract, dropped in year 1 (index 0) -> 3 - 0 = 3 penalties
        # Example: 3yr contract, dropped in year 2 (index 1) -> 3 - 1 = 2 penalties
        # (year_dropped - contract_start_year) is the 0-indexed year *into* the contract that the drop occurred.
        if year_dropped < contract_start_year or year_dropped >= contract_start_year + contract_duration:
            logger.warning(f"Contract {contract_row_id}: year_dropped ({year_dropped}) is outside of contract term ({contract_start_year} - {contract_start_year + contract_duration - 1}). No penalties applied.")
            num_penalty_application_periods = 0
        else:
            num_penalty_application_periods = contract_duration - (year_dropped - contract_start_year)
        
        logger.info(f"Contract {contract_row_id}: num_penalty_application_periods = {num_penalty_application_periods}")

        penalties_to_apply = []
        if num_penalty_application_periods > 0:
            original_escalated_costs_list = get_escalated_contract_costs(draft_amount, contract_duration, contract_start_year)
            logger.debug(f"Contract {contract_row_id}: Original escalated costs: {original_escalated_costs_list}")

            for j in range(num_penalty_application_periods):
                penalty_hit_calendar_year = first_actual_penalty_hit_year + j

                # Determine the cost basis for this j-th penalty installment.
                # It's based on the player's value for the (year_dropped - contract_start_year + j)-th year *of their original contract term commitment*,
                # plus one year to look ahead to the year whose salary is being penalized.
                # Example: Dropped in year 1 (index 0) of contract. 
                #   j=0 (1st penalty): basis from original contract year index 0+1 = 1 (2nd year salary)
                #   j=1 (2nd penalty): basis from original contract year index 1+1 = 2 (3rd year salary)
                #   j=2 (3rd penalty): basis from original contract year index 2+1 = 3 (4th year salary - projected)
                
                # This index points to which year OF THE ORIGINAL CONTRACT defines the salary base for this penalty installment
                # The value `year_dropped - contract_start_year` is the 0-indexed year *into* the contract when the drop happened.
                # We are interested in the salary of the *next* year in the contract sequence for the first penalty, then the year after, etc.
                effective_contract_year_index_for_cost_basis = (year_dropped - contract_start_year) + j + 1

                cost_for_basis = 0.0
                if effective_contract_year_index_for_cost_basis < contract_duration:
                    # Cost basis is from a year within the original contract term
                    cost_for_basis = original_escalated_costs_list[effective_contract_year_index_for_cost_basis]['cost']
                    logger.debug(f"  Penalty {j+1} (hits {penalty_hit_calendar_year}): basis from original contract year {effective_contract_year_index_for_cost_basis + contract_start_year} (index {effective_contract_year_index_for_cost_basis}), cost={cost_for_basis}")
                else:
                    # Cost basis is for a year beyond the original contract term (e.g., the "2028" in the example)
                    # We need to project it from the last known cost.
                    if not original_escalated_costs_list: # Should not happen if contract_duration > 0
                         logger.error(f"Contract {contract_row_id}: Cannot project future cost, original_escalated_costs_list is empty.")
                         continue # Skip this penalty installment
                    
                    last_original_cost = original_escalated_costs_list[-1]['cost']
                    num_years_to_project_beyond = effective_contract_year_index_for_cost_basis - (contract_duration - 1)
                    
                    projected_cost = last_original_cost
                    for _ in range(num_years_to_project_beyond):
                        projected_cost = math.ceil(projected_cost * 1.1)
                    cost_for_basis = projected_cost
                    logger.debug(f"  Penalty {j+1} (hits {penalty_hit_calendar_year}): basis projected for effective year index {effective_contract_year_index_for_cost_basis}, cost={cost_for_basis}")

                penalty_amount = max(1, round(cost_for_basis * 0.25)) # 25% of that year's cost, rounded normally, minimum 1
                penalties_to_apply.append({'year': penalty_hit_calendar_year, 'amount': penalty_amount})
        
        logger.info(f"apply_contract_penalties_and_deactivate: Calculated penalties for contract_row_id {contract_row_id}: {penalties_to_apply}")

        for penalty_detail in penalties_to_apply:
            penalty_year = penalty_detail['year']
            penalty_amount_dollars = penalty_detail['amount'] 

            logger.debug(f"apply_contract_penalties_and_deactivate: Applying penalty: Year {penalty_year}, Amount (dollars) {penalty_amount_dollars} for contract {contract_row_id}")
            cursor.execute('''
                INSERT INTO penalties (contract_id, penalty_year, penalty_amount, created_at, updated_at)
                VALUES (?, ?, ?, datetime('now'), datetime('now'))
            ''', (contract_row_id, penalty_year, penalty_amount_dollars))
            logger.debug(f"apply_contract_penalties_and_deactivate: Penalty record inserted for year {penalty_year}, contract {contract_row_id}")

        # Deactivate contract
        logger.debug(f"apply_contract_penalties_and_deactivate: Deactivating contract_row_id {contract_row_id}")
        cursor.execute("UPDATE contracts SET is_active = 0, updated_at = datetime('now') WHERE rowid = ?", (contract_row_id,))
        logger.debug(f"apply_contract_penalties_and_deactivate: Contract {contract_row_id} deactivated.")
        
        logger.info(f"Successfully applied {len(penalties_to_apply)} penalties and deactivated contract_row_id {contract_row_id}.")
    
    except Exception as e:
        logger.error(f"apply_contract_penalties_and_deactivate: Error processing contract_row_id {contract_row_id}: {e}")
        # import traceback # Optional: for more detailed logging if needed
        # logger.error(traceback.format_exc())
        raise # Re-raise the exception to be caught by the caller

# Example usage (for testing or if called directly, though normally via SleeperService)
# ... existing code ... 