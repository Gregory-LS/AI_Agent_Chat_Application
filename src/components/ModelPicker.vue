<template>
  <div class="model-picker">
    <div class="header">
      <h3>Select Model</h3>
      <button @click="toggleFavorites">
        {{ showFavorites ? 'Show All' : 'Show Favorites' }}
      </button>
    </div>
    <div class="model-list">
      <div 
        v-for="model in filteredModels" 
        :key="model.id" 
        class="model-item"
        :class="{ 'favorite': model.favorite, 'recent': isRecent(model) }"
        @click="selectModel(model)"
      >
        <div class="model-meta">
          <h4>{{ model.name }}</h4>
          <p>{{ model.description }}</p>
          <p><strong>Parameters:</strong> {{ model.parameters }}</p>
          <p><strong>Size:</strong> {{ model.size }}</p>
        </div>
        <button 
          class="favorite-btn" 
          @click.stop="toggleFavorite(model)"
        >
          {{ model.favorite ? '★' : '☆' }}
        </button>
      </div>
    </div>
    <div class="footer">
      <p>Selected Model: {{ selectedModel ? selectedModel.name : 'None' }}</p>
    </div>
  </div>
</template>

<script>
export default {
  props: {
    models: {
      type: Array,
      required: true
    },
    conversationId: {
      type: String,
      required: true
    }
  },
  data() {
    return {
      showFavorites: false,
      selectedModel: null,
      recentlyUsed: [],
      favorites: JSON.parse(localStorage.getItem('favoriteModels') || '[]')
    }
  },
  computed: {
    filteredModels() {
      return this.showFavorites 
        ? this.models.filter(model => this.favorites.includes(model.id))
        : this.models
    }
  },
  watch: {
    conversationId: {
      handler: 'loadConversationModel',
      immediate: true
    }
  },
  methods: {
    selectModel(model) {
      this.selectedModel = model
      this.$emit('model-selected', model)
      this.addToRecentlyUsed(model)
      this.saveConversationModel()
    },
    toggleFavorite(model) {
      const index = this.favorites.indexOf(model.id)
      if (index === -1) {
        this.favorites.push(model.id)
      } else {
        this.favorites.splice(index, 1)
      }
      localStorage.setItem('favoriteModels', JSON.stringify(this.favorites))
    },
    toggleFavorites() {
      this.showFavorites = !this.showFavorites
    },
    isRecent(model) {
      return this.recentlyUsed.includes(model.id)
    },
    addToRecentlyUsed(model) {
      if (!this.recentlyUsed.includes(model.id)) {
        this.recentlyUsed.unshift(model.id)
        if (this.recentlyUsed.length > 5) {
          this.recentlyUsed.pop()
        }
      }
    },
    loadConversationModel() {
      const savedModelId = localStorage.getItem(`model_${this.conversationId}`)
      if (savedModelId) {
        const model = this.models.find(m => m.id === savedModelId)
        if (model) {
          this.selectedModel = model
          this.$emit('model-selected', model)
        }
      }
    },
    saveConversationModel() {
      if (this.selectedModel) {
        localStorage.setItem(`model_${this.conversationId}`, this.selectedModel.id)
      }
    }
  }
}
</script>

<style scoped>
.model-picker {
  border: 1px solid #ccc;
  padding: 1rem;
}
.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}
.model-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}
.model-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.5rem;
  border: 1px solid #ddd;
  cursor: pointer;
}
.model-item:hover {
  background-color: #f5f5f5;
}
.model-item.favorite {
  border-color: gold;
}
.model-item.recent {
  border-color: #90caf9;
}
.model-meta {
  flex: 1;
}
.favorite-btn {
  background: none;
  border: none;
  font-size: 1.2rem;
  cursor: pointer;
}
.footer {
  margin-top: 1rem;
}
</style>