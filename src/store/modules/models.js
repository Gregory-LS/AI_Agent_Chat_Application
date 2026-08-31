export default {
  state: {
    models: [
      {
        id: 'gpt-4',
        name: 'GPT-4',
        description: 'Most capable model, great for complex tasks',
        parameters: '175B',
        size: '800GB',
        favorite: false
      },
      {
        id: 'gpt-3.5-turbo',
        name: 'GPT-3.5 Turbo',
        description: 'Fast and cost-effective for simple tasks',
        parameters: '6B',
        size: '350GB',
        favorite: false
      }
    ]
  },
  mutations: {
    ADD_MODEL(state, model) {
      state.models.push(model)
    }
  },
  actions: {
    addModel({ commit }, model) {
      commit('ADD_MODEL', model)
    }
  },
  getters: {
    allModels: state => state.models,
    favoriteModels: state => state.models.filter(model => model.favorite)
  }
}