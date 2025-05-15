<template>
  <div class="sleeper-import">
    <div class="search-section">
      <h2>Import Sleeper League</h2>
      <div class="search-box">
        <input 
          v-model="username" 
          type="text" 
          placeholder="Enter Sleeper username"
          @keyup.enter="searchLeagues"
        />
        <button @click="searchLeagues" :disabled="isLoading">
          {{ isLoading ? 'Searching...' : 'Search' }}
        </button>
      </div>
    </div>

    <div v-if="error" class="error-message">
      {{ error }}
    </div>

    <div v-if="user" class="user-info">
      <h3>User Found: {{ user.display_name }}</h3>
    </div>

    <div v-if="leagues.length > 0" class="leagues-list">
      <h3>Available Leagues</h3>
      <div class="league-cards">
        <div v-for="league in leagues" :key="league.league_id" class="league-card">
          <div class="league-info">
            <h4>{{ league.name }}</h4>
            <p>Season: {{ league.season }}</p>
            <p>Status: {{ league.status }}</p>
          </div>
          <button 
            @click="importLeague(league.league_id)"
            :disabled="isImporting"
            class="import-button"
          >
            {{ isImporting ? 'Importing...' : 'Import League' }}
          </button>
        </div>
      </div>
    </div>

    <div v-if="!leagues.length && searched" class="no-leagues">
      No leagues found for this user.
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'

const router = useRouter()
const username = ref('')
const user = ref(null)
const leagues = ref([])
const error = ref('')
const isLoading = ref(false)
const isImporting = ref(false)
const searched = ref(false)

const searchLeagues = async () => {
  if (!username.value) {
    error.value = 'Please enter a username'
    return
  }

  error.value = ''
  isLoading.value = true
  searched.value = true

  try {
    const response = await axios.get(`/sleeper/search?username=${username.value}`)
    if (response.data.success) {
      user.value = response.data.user
      leagues.value = response.data.leagues
    } else {
      error.value = response.data.error || 'Failed to fetch leagues'
    }
  } catch (err) {
    error.value = err.response?.data?.error || 'An error occurred while searching'
  } finally {
    isLoading.value = false
  }
}

const importLeague = async (leagueId) => {
  error.value = ''
  isImporting.value = true

  try {
    const response = await axios.post('/sleeper/import', { league_id: leagueId })
    if (response.data.success) {
      // Redirect to the league page after successful import
      router.push(`/league/${response.data.league_id}`)
    } else {
      error.value = response.data.error || 'Failed to import league'
    }
  } catch (err) {
    error.value = err.response?.data?.error || 'An error occurred while importing'
  } finally {
    isImporting.value = false
  }
}
</script>

<style scoped>
.sleeper-import {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
}

.search-section {
  margin-bottom: 30px;
}

.search-box {
  display: flex;
  gap: 10px;
  margin-top: 15px;
}

input {
  flex: 1;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 16px;
}

button {
  padding: 10px 20px;
  background-color: #4CAF50;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 16px;
  transition: background-color 0.3s;
}

button:disabled {
  background-color: #cccccc;
  cursor: not-allowed;
}

button:hover:not(:disabled) {
  background-color: #45a049;
}

.error-message {
  color: #ff0000;
  margin: 10px 0;
  padding: 10px;
  background-color: #ffe6e6;
  border-radius: 4px;
}

.user-info {
  margin: 20px 0;
  padding: 15px;
  background-color: #f5f5f5;
  border-radius: 4px;
}

.leagues-list {
  margin-top: 30px;
}

.league-cards {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
  margin-top: 15px;
}

.league-card {
  border: 1px solid #ddd;
  border-radius: 8px;
  padding: 15px;
  background-color: white;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.league-info {
  margin-bottom: 15px;
}

.league-info h4 {
  margin: 0 0 10px 0;
  color: #333;
}

.league-info p {
  margin: 5px 0;
  color: #666;
}

.import-button {
  width: 100%;
  margin-top: 10px;
}

.no-leagues {
  text-align: center;
  color: #666;
  margin-top: 20px;
  padding: 20px;
  background-color: #f5f5f5;
  border-radius: 4px;
}
</style> 