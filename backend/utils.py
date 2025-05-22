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
    db_conn: sqlite3.Connection, 
    logger: logging.Logger
):
    # Ensure logger is available
    if not logger:
        # Fallback to a default logger if None is provided, though it's better to ensure it's always passed.
        logger = logging.getLogger(__name__)
        logger.warning("apply_contract_penalties_and_deactivate: Logger not provided, using default.")

    cursor = db_conn.cursor()
    try:
        # Ensure proper type conversion for years if not already done
        contract_start_year = int(contract_start_year)
        year_dropped = int(year_dropped)
        contract_duration = int(contract_duration)

        penalties_to_apply = []
        # Calculate penalties for each remaining year of the contract, starting from year_dropped
        # A contract year is, e.g., 2025. Duration is number of years.
        # If contract starts 2025, duration 3, it covers 2025, 2026, 2027.
        # If dropped in 2025 (before/during year 1), penalties for 2025, 2026, 2027.
        # If dropped in 2026 (before/during year 2), penalties for 2026, 2027.
        
        # Get escalated costs first
        escalated_costs = get_escalated_contract_costs(draft_amount, contract_duration, contract_start_year)
        # logger.debug(f"apply_contract_penalties_and_deactivate: Escalated costs for contract {contract_row_id}: {escalated_costs}")


        for year_cost_detail in escalated_costs:
            contract_specific_year = year_cost_detail['year']
            year_specific_cost = year_cost_detail['cost']

            if contract_specific_year >= year_dropped:
                # Penalty is 10% of the cost for *that specific year*, rounded up
                penalty_for_year_cents = math.ceil(year_specific_cost * 0.10) # Assuming cost is in dollars, convert to cents
                
                # Store as integer cents
                penalties_to_apply.append({'year': contract_specific_year, 'amount_cents': int(penalty_for_year_cents)})
        
        logger.info(f"apply_contract_penalties_and_deactivate: Calculated penalties for contract_row_id {contract_row_id} (dropped in {year_dropped}): {penalties_to_apply}")

        for penalty_detail in penalties_to_apply:
            penalty_year = penalty_detail['year']
            penalty_amount_dollars = penalty_detail['amount_cents'] # Name is amount_cents, but value is dollars from math.ceil(cost * 0.10)

            # logger.debug(f"apply_contract_penalties_and_deactivate: Applying penalty: Year {penalty_year}, Amount (dollars) {penalty_amount_dollars} for contract {contract_row_id}")
            cursor.execute('''
                INSERT INTO penalties (contract_id, penalty_year, penalty_amount, created_at, updated_at)
                VALUES (?, ?, ?, datetime('now'), datetime('now'))
            ''', (contract_row_id, penalty_year, penalty_amount_dollars))
            # logger.debug(f"apply_contract_penalties_and_deactivate: Penalty record inserted for year {penalty_year}, contract {contract_row_id}")

        # Deactivate contract
        # logger.debug(f"apply_contract_penalties_and_deactivate: Deactivating contract_row_id {contract_row_id}")
        cursor.execute("UPDATE contracts SET is_active = 0, updated_at = datetime('now') WHERE id = ?", (contract_row_id,))
        # logger.debug(f"apply_contract_penalties_and_deactivate: Contract {contract_row_id} deactivated.")
        
        logger.info(f"Successfully applied {len(penalties_to_apply)} penalties and deactivated contract_row_id {contract_row_id}.")
    
    except Exception as e:
        logger.error(f"apply_contract_penalties_and_deactivate: Error processing contract_row_id {contract_row_id}: {e}")
        # import traceback # Optional: for more detailed logging if needed
        # logger.error(traceback.format_exc())
        raise # Re-raise the exception to be caught by the caller

# Example usage (for testing or if called directly, though normally via SleeperService)
# ... existing code ... 