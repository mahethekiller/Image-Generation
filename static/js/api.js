/**
 * API Service for AetherGen
 * Real API endpoint calls without mock data
 */

const API = {
  async getKeysConfig() {
    const res = await fetch('/api/config/keys');
    if (!res.ok) throw new Error('Failed to fetch key configuration status.');
    return await res.json();
  },

  async saveApiKey(provider, apiKey) {
    const res = await fetch('/api/config/save-key', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ provider, api_key: apiKey })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Failed to save API key.');
    return data;
  },

  async syncModels(provider, apiKey = '') {
    const res = await fetch('/api/models/sync', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ provider, api_key: apiKey })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Failed to sync models.');
    return { models: data.models || [], source: data.source || 'env' };
  },

  async getPromptCategories() {
    const res = await fetch('/api/prompt/categories');
    if (!res.ok) throw new Error('Failed to load prompt categories.');
    return await res.json();
  },

  async enhancePrompt(prompt, provider = 'openai', apiKey = '', style = 'cinematic') {
    const res = await fetch('/api/prompt/enhance', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ prompt, provider, api_key: apiKey, style })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Failed to enhance prompt.');
    return data.enhanced;
  },

  async getGameAssetTypes() {
    const res = await fetch('/api/game-asset/types');
    if (!res.ok) throw new Error('Failed to load game asset types.');
    return await res.json();
  },

  async generateStandardImage(params) {
    const res = await fetch('/api/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(params)
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Image generation failed.');
    return data.data;
  },

  async generateGameAsset(params) {
    const res = await fetch('/api/game-asset/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(params)
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Game asset generation failed.');
    return data.data;
  },

  async removeBackground(generationId) {
    const res = await fetch(`/api/game-asset/remove-bg/${generationId}`, {
      method: 'POST'
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Background removal failed.');
    return data.data;
  },

  async getHistory() {
    const res = await fetch('/api/history');
    if (!res.ok) throw new Error('Failed to fetch history.');
    return await res.json();
  }
};
