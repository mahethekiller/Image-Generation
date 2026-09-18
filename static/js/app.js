/**
 * AetherGen Main Application Logic
 */

document.addEventListener('DOMContentLoaded', async () => {
  // State
  const state = {
    mode: 'standard', // 'standard' | 'game'
    provider: 'openai', // 'openai' | 'gemini'
    models: [],
    selectedModel: '',
    selectedAssetType: 'character_sprite',
    selectedAspect: '1:1',
    promptCategories: {},
    activeCategory: 'Lighting',
    keysConfig: { openai: { has_key: false }, gemini: { has_key: false } },
    currentGeneration: null,
    isGenerating: false,
    timerInterval: null
  };

  // DOM Elements
  const el = {
    // Navigation
    navStandard: document.getElementById('navStandard'),
    navGame: document.getElementById('navGame'),
    keyStatusBadge: document.getElementById('keyStatusBadge'),
    statusSummary: document.getElementById('statusSummary'),
    btnOpenKeyModal: document.getElementById('btnOpenKeyModal'),

    // Provider & Model
    providerBtns: document.querySelectorAll('.provider-btn'),
    btnSyncModels: document.getElementById('btnSyncModels'),
    modelsCountBadge: document.getElementById('modelsCountBadge'),
    modelSelect: document.getElementById('modelSelect'),
    currentApiKey: document.getElementById('currentApiKey'),
    btnToggleKeyVisibility: document.getElementById('btnToggleKeyVisibility'),
    btnSaveActiveKey: document.getElementById('btnSaveActiveKey'),
    envIndicator: document.getElementById('envIndicator'),

    // Game Asset Studio
    gameAssetConfigCard: document.getElementById('gameAssetConfigCard'),
    gameAssetTypesGrid: document.getElementById('gameAssetTypesGrid'),
    autoRemoveBgCheckbox: document.getElementById('autoRemoveBgCheckbox'),

    // Prompt & Modifiers
    promptInput: document.getElementById('promptInput'),
    negativePromptInput: document.getElementById('negativePromptInput'),
    btnAiEnhancePrompt: document.getElementById('btnAiEnhancePrompt'),
    chipCategoryTabs: document.getElementById('chipCategoryTabs'),
    chipsContainer: document.getElementById('chipsContainer'),
    aspectBtns: document.querySelectorAll('.aspect-btn'),
    qualityWrapper: document.getElementById('qualityWrapper'),
    qualitySelect: document.getElementById('qualitySelect'),
    btnGenerate: document.getElementById('btnGenerate'),
    btnGenerateText: document.getElementById('btnGenerateText'),

    // Viewport & Canvas
    viewportBadge: document.getElementById('viewportBadge'),
    viewportInfo: document.getElementById('viewportInfo'),
    viewModeToggleGroup: document.getElementById('viewModeToggleGroup'),
    btnViewOriginal: document.getElementById('btnViewOriginal'),
    btnViewTransparent: document.getElementById('btnViewTransparent'),
    btnManualRemoveBg: document.getElementById('btnManualRemoveBg'),
    btnTopDownloadOriginal: document.getElementById('btnTopDownloadOriginal'),
    btnTopDownloadTransparent: document.getElementById('btnTopDownloadTransparent'),
    viewportStage: document.getElementById('viewportStage'),
    stagePlaceholder: document.getElementById('stagePlaceholder'),
    stageLoader: document.getElementById('stageLoader'),
    loaderTitle: document.getElementById('loaderTitle'),
    loaderTimer: document.getElementById('loaderTimer'),
    stageImageContainer: document.getElementById('stageImageContainer'),
    mainResultImage: document.getElementById('mainResultImage'),
    overlayDownloadBtn: document.getElementById('overlayDownloadBtn'),
    overlayViewFullBtn: document.getElementById('overlayViewFullBtn'),

    // Footer & Actions
    metaPromptText: document.getElementById('metaPromptText'),
    btnCopyPrompt: document.getElementById('btnCopyPrompt'),
    btnDownloadOriginal: document.getElementById('btnDownloadOriginal'),
    btnDownloadTransparent: document.getElementById('btnDownloadTransparent'),

    // History
    historyGrid: document.getElementById('historyGrid'),
    historyCount: document.getElementById('historyCount'),

    // Key Modal
    keyModal: document.getElementById('keyModal'),
    btnCloseKeyModal: document.getElementById('btnCloseKeyModal'),
    btnDoneKeyModal: document.getElementById('btnDoneKeyModal'),
    modalOpenAiKey: document.getElementById('modalOpenAiKey'),
    modalGeminiKey: document.getElementById('modalGeminiKey'),
    modalOpenAiStatus: document.getElementById('modalOpenAiStatus'),
    modalGeminiStatus: document.getElementById('modalGeminiStatus'),
    btnSaveOpenAiModal: document.getElementById('btnSaveOpenAiModal'),
    btnSaveGeminiModal: document.getElementById('btnSaveGeminiModal'),

    toastContainer: document.getElementById('toastContainer')
  };

  // Toast notification helper
  function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    let icon = 'ℹ️';
    if (type === 'success') icon = '✅';
    if (type === 'error') icon = '⚠️';
    toast.innerHTML = `<span>${icon}</span> <span>${message}</span>`;
    el.toastContainer.appendChild(toast);
    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateY(10px)';
      setTimeout(() => toast.remove(), 250);
    }, 4000);
  }

  // Initial Data Fetch
  async function init() {
    await refreshKeyStatus();
    await loadPromptCategories();
    await loadGameAssetTypes();
    await syncProviderModels(true);
    const historyList = await refreshHistory();
    if (historyList && historyList.length > 0) {
      loadGenerationIntoStage(historyList[0]);
    }
    setupEventListeners();
  }

  // Refresh status of .env keys
  async function refreshKeyStatus() {
    try {
      const config = await API.getKeysConfig();
      state.keysConfig = config;

      // Update header badge and input placeholder
      const activeProviderKey = config[state.provider];
      const statusDot = el.keyStatusBadge.querySelector('.status-dot');
      if (activeProviderKey && activeProviderKey.has_key) {
        statusDot.classList.add('active');
        el.statusSummary.textContent = `${state.provider.toUpperCase()} Ready (.env)`;
        el.envIndicator.textContent = `💾 Using key from .env (${activeProviderKey.preview})`;
        el.currentApiKey.placeholder = `Using key from .env (${activeProviderKey.preview}) — or type new key`;
      } else {
        statusDot.classList.remove('active');
        el.statusSummary.textContent = `No ${state.provider.toUpperCase()} Key`;
        el.envIndicator.textContent = `⚠️ No key found in .env`;
        el.currentApiKey.placeholder = `Enter ${state.provider.toUpperCase()} API key to sync or save...`;
      }

      // Update modal badges
      if (config.openai.has_key) {
        el.modalOpenAiStatus.textContent = `Saved (${config.openai.preview})`;
        el.modalOpenAiStatus.className = 'field-badge configured';
      } else {
        el.modalOpenAiStatus.textContent = 'Not configured';
        el.modalOpenAiStatus.className = 'field-badge';
      }

      if (config.gemini.has_key) {
        el.modalGeminiStatus.textContent = `Saved (${config.gemini.preview})`;
        el.modalGeminiStatus.className = 'field-badge configured';
      } else {
        el.modalGeminiStatus.textContent = 'Not configured';
        el.modalGeminiStatus.className = 'field-badge';
      }
    } catch (err) {
      console.error('Error fetching key status:', err);
    }
  }

  // Load Prompt Modifiers / Chips
  async function loadPromptCategories() {
    try {
      state.promptCategories = await API.getPromptCategories();
      renderChips(state.activeCategory);
    } catch (err) {
      console.error('Failed to load categories', err);
    }
  }

  function renderChips(categoryName) {
    el.chipsContainer.innerHTML = '';
    const items = state.promptCategories[categoryName] || [];
    items.forEach(token => {
      const chip = document.createElement('button');
      chip.type = 'button';
      chip.className = 'prompt-chip';
      chip.textContent = token;
      chip.addEventListener('click', () => appendToPrompt(token));
      el.chipsContainer.appendChild(chip);
    });
  }

  function appendToPrompt(text) {
    const current = el.promptInput.value.trim();
    if (!current) {
      el.promptInput.value = text;
    } else if (!current.toLowerCase().includes(text.toLowerCase())) {
      el.promptInput.value = `${current}, ${text}`;
    }
    el.promptInput.focus();
    showToast(`Added "${text}" to prompt`, 'info');
  }

  // Load Game Asset Presets
  async function loadGameAssetTypes() {
    try {
      const types = await API.getGameAssetTypes();
      el.gameAssetTypesGrid.innerHTML = '';
      Object.keys(types).forEach((key, index) => {
        const item = types[key];
        const card = document.createElement('div');
        card.className = `asset-card ${index === 0 ? 'active' : ''}`;
        card.dataset.key = key;
        card.innerHTML = `
          <span class="asset-icon">${item.icon}</span>
          <span class="asset-label">${item.name}</span>
        `;
        card.addEventListener('click', () => {
          document.querySelectorAll('.asset-card').forEach(c => c.classList.remove('active'));
          card.classList.add('active');
          state.selectedAssetType = key;
        });
        el.gameAssetTypesGrid.appendChild(card);
      });
    } catch (err) {
      console.error('Failed to load game asset types', err);
    }
  }

  // Dynamic Model Syncing (Uses .env key or custom input)
  async function syncProviderModels(isInitial = false) {
    const btn = el.btnSyncModels;
    btn.classList.add('spinning');
    el.modelsCountBadge.textContent = 'Syncing...';
    el.modelSelect.innerHTML = `<option value="">Fetching live models from ${state.provider.toUpperCase()}...</option>`;

    const customKey = el.currentApiKey.value.trim();

    try {
      const response = await API.syncModels(state.provider, customKey);
      const models = response.models || [];
      const source = response.source || (customKey ? 'input' : 'env');
      state.models = models;
      el.modelSelect.innerHTML = '';

      if (models.length === 0) {
        el.modelSelect.innerHTML = '<option value="">No models available</option>';
        el.modelsCountBadge.textContent = '0 Models';
        if (!isInitial) showToast(`No image models returned by ${state.provider.toUpperCase()}`, 'error');
        return;
      }

      // Populate select dropdown with real models
      models.forEach(m => {
        const opt = document.createElement('option');
        opt.value = m.id;
        const desc = m.description ? ` — ${m.description}` : '';
        opt.textContent = `${m.name}${desc}`;
        el.modelSelect.appendChild(opt);
      });

      // Intelligently select default preferred model
      const preferred = state.provider === 'openai' ? 'dall-e-3' : 'imagen-3.0-generate-002';
      const hasPreferred = models.some(m => m.id === preferred);
      state.selectedModel = hasPreferred ? preferred : models[0].id;
      el.modelSelect.value = state.selectedModel;

      // Update badge
      const sourceLabel = source === 'env' ? '.env key' : 'input key';
      el.modelsCountBadge.textContent = `✅ ${models.length} Models Synced (${sourceLabel})`;

      // Trigger brief pulse animation on dropdown so user sees it populated
      el.modelSelect.classList.remove('model-select-highlight');
      void el.modelSelect.offsetWidth; // trigger reflow
      el.modelSelect.classList.add('model-select-highlight');

      if (!isInitial) {
        showToast(`Synced ${models.length} models from ${state.provider.toUpperCase()} (using ${sourceLabel})!`, 'success');
      }
    } catch (err) {
      el.modelSelect.innerHTML = '<option value="">Sync failed — check key</option>';
      el.modelsCountBadge.textContent = 'Sync Failed';
      if (!isInitial) {
        showToast(err.message, 'error');
      }
    } finally {
      btn.classList.remove('spinning');
    }
  }

  // History loader
  async function refreshHistory() {
    try {
      const list = await API.getHistory();
      el.historyCount.textContent = `${list.length} generated`;
      if (list.length === 0) {
        el.historyGrid.innerHTML = '<div class="history-empty">Your generated images and game sprites will appear here.</div>';
        return;
      }

      el.historyGrid.innerHTML = '';
      list.forEach(item => {
        const div = document.createElement('div');
        div.className = 'history-item';
        div.title = `${item.model}: ${item.prompt}`;
        const badgeText = item.mode.startsWith('game_asset') ? 'Sprite' : 'Standard';
        div.innerHTML = `
          <img class="history-thumb" src="${item.image_url}" alt="Thumbnail">
          <span class="history-badge">${badgeText}</span>
          <a class="history-dl-btn" href="/api/download/${item.id}?format=original" download title="Download Image">📥</a>
        `;
        div.addEventListener('click', (e) => {
          if (e.target.closest('.history-dl-btn')) return;
          loadGenerationIntoStage(item);
        });
        el.historyGrid.appendChild(div);
      });
      return list;
    } catch (err) {
      console.error('History load error', err);
      return [];
    }
  }

  // Display Generation in Viewport
  function loadGenerationIntoStage(item) {
    if (!item) return;
    state.currentGeneration = item;
    el.stagePlaceholder.classList.add('hidden');
    el.stageLoader.classList.add('hidden');
    el.stageImageContainer.classList.remove('hidden');

    // Ensure image is displayed
    el.mainResultImage.style.display = 'block';
    el.mainResultImage.src = item.image_url;
    el.viewportBadge.textContent = item.mode.startsWith('game_asset') ? 'Game Asset' : 'Image Render';
    el.viewportInfo.textContent = `${item.provider.toUpperCase()} • ${item.model} • ${item.aspect_ratio || '1:1'}`;
    el.metaPromptText.textContent = `"${item.prompt}"`;

    // Download Links
    const dlOriginalUrl = `/api/download/${item.id}?format=original`;
    
    // Bottom Footer Button
    el.btnDownloadOriginal.href = dlOriginalUrl;
    el.btnDownloadOriginal.style.pointerEvents = 'auto';
    el.btnDownloadOriginal.style.opacity = '1';
    el.btnCopyPrompt.disabled = false;

    // Top Toolbar Download Button
    if (el.btnTopDownloadOriginal) {
      el.btnTopDownloadOriginal.href = dlOriginalUrl;
      el.btnTopDownloadOriginal.classList.remove('hidden');
    }

    // Image Overlay Links
    if (el.overlayDownloadBtn) {
      el.overlayDownloadBtn.href = dlOriginalUrl;
    }
    if (el.overlayViewFullBtn) {
      el.overlayViewFullBtn.href = item.image_url;
    }

    // Transparent Sprite controls
    if (item.transparent_filename) {
      const dlTransUrl = `/api/download/${item.id}?format=transparent`;
      el.btnViewTransparent.disabled = false;
      el.btnDownloadTransparent.href = dlTransUrl;
      el.btnDownloadTransparent.classList.remove('hidden');
      if (el.btnTopDownloadTransparent) {
        el.btnTopDownloadTransparent.href = dlTransUrl;
        el.btnTopDownloadTransparent.classList.remove('hidden');
      }
      el.btnManualRemoveBg.disabled = true;
      el.btnManualRemoveBg.textContent = 'Alpha Extracted ✓';
    } else {
      el.btnViewTransparent.disabled = true;
      el.btnDownloadTransparent.classList.add('hidden');
      if (el.btnTopDownloadTransparent) {
        el.btnTopDownloadTransparent.classList.add('hidden');
      }
      el.btnManualRemoveBg.disabled = false;
      el.btnManualRemoveBg.textContent = '🪄 Extract Alpha';
    }

    // Default to original view
    switchToViewMode('original');
  }

  function switchToViewMode(mode) {
    if (!state.currentGeneration) return;
    if (mode === 'transparent' && state.currentGeneration.transparent_url) {
      el.mainResultImage.src = state.currentGeneration.transparent_url;
      el.viewportStage.classList.add('checkerboard');
      el.btnViewTransparent.classList.add('active');
      el.btnViewOriginal.classList.remove('active');
    } else {
      el.mainResultImage.src = state.currentGeneration.image_url;
      el.viewportStage.classList.remove('checkerboard');
      el.btnViewOriginal.classList.add('active');
      el.btnViewTransparent.classList.remove('active');
    }
  }

  // Generation Execution
  async function handleGenerate() {
    const prompt = el.promptInput.value.trim();
    if (!prompt) {
      showToast('Please enter an image prompt first!', 'error');
      el.promptInput.focus();
      return;
    }

    const model = el.modelSelect.value || state.selectedModel;
    if (!model) {
      showToast('No active model selected. Please sync models first.', 'error');
      return;
    }

    // Set Loading UI
    state.isGenerating = true;
    el.btnGenerate.disabled = true;
    el.btnGenerateText.textContent = 'Synthesizing with AI...';
    el.stagePlaceholder.classList.add('hidden');
    el.stageImageContainer.classList.add('hidden');
    el.stageLoader.classList.remove('hidden');

    const startTime = Date.now();
    el.loaderTimer.textContent = '0.0s';
    clearInterval(state.timerInterval);
    state.timerInterval = setInterval(() => {
      const elapsed = ((Date.now() - startTime) / 1000).toFixed(1);
      el.loaderTimer.textContent = `${elapsed}s`;
    }, 100);

    const customKey = el.currentApiKey.value.trim();

    try {
      let result;
      if (state.mode === 'game') {
        el.loaderTitle.textContent = 'Generating Game Sprite & Environment Asset...';
        result = await API.generateGameAsset({
          provider: state.provider,
          api_key: customKey || null,
          model: model,
          prompt: prompt,
          asset_type: state.selectedAssetType,
          aspect_ratio: state.selectedAspect,
          auto_remove_bg: el.autoRemoveBgCheckbox.checked
        });
      } else {
        el.loaderTitle.textContent = `Rendering with ${state.provider.toUpperCase()} (${model})...`;
        result = await API.generateStandardImage({
          provider: state.provider,
          api_key: customKey || null,
          model: model,
          prompt: prompt,
          negative_prompt: el.negativePromptInput.value.trim(),
          aspect_ratio: state.selectedAspect,
          quality: el.qualitySelect.value,
          mode: 'standard'
        });
      }

      loadGenerationIntoStage(result);
      await refreshHistory();
      showToast('Generation complete! Image ready.', 'success');
    } catch (err) {
      el.stageLoader.classList.add('hidden');
      el.stagePlaceholder.classList.remove('hidden');
      showToast(err.message, 'error');
    } finally {
      clearInterval(state.timerInterval);
      state.isGenerating = false;
      el.btnGenerate.disabled = false;
      el.btnGenerateText.textContent = state.mode === 'game' ? 'Generate Game Asset' : 'Generate Real Image';
    }
  }

  // Event Listeners
  function setupEventListeners() {
    // Mode Navigation
    el.navStandard.addEventListener('click', () => {
      state.mode = 'standard';
      el.navStandard.classList.add('active');
      el.navGame.classList.remove('active');
      el.gameAssetConfigCard.classList.add('hidden');
      el.btnGenerateText.textContent = 'Generate Real Image';
    });

    el.navGame.addEventListener('click', () => {
      state.mode = 'game';
      el.navGame.classList.add('active');
      el.navStandard.classList.remove('active');
      el.gameAssetConfigCard.classList.remove('hidden');
      el.btnGenerateText.textContent = 'Generate Game Asset';
    });

    // Provider Selector
    el.providerBtns.forEach(btn => {
      btn.addEventListener('click', async () => {
        el.providerBtns.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        state.provider = btn.dataset.provider;
        
        // Toggle quality dropdown only for OpenAI DALL-E 3
        if (state.provider === 'openai') {
          el.qualityWrapper.classList.remove('hidden');
        } else {
          el.qualityWrapper.classList.add('hidden');
        }

        // Clear custom key input on switch so it cleanly uses the selected provider's .env key
        el.currentApiKey.value = '';
        await refreshKeyStatus();
        await syncProviderModels(false);
      });
    });

    // Sync Models Button
    el.btnSyncModels.addEventListener('click', () => syncProviderModels(false));

    // Save Active Key directly to .env
    el.btnSaveActiveKey.addEventListener('click', async () => {
      const key = el.currentApiKey.value.trim();
      if (!key) {
        showToast('Please enter an API key to save.', 'error');
        return;
      }
      try {
        await API.saveApiKey(state.provider, key);
        showToast(`Saved ${state.provider.toUpperCase()} key directly to .env!`, 'success');
        el.currentApiKey.value = '';
        await refreshKeyStatus();
        await syncProviderModels(false);
      } catch (err) {
        showToast(err.message, 'error');
      }
    });

    // Toggle Key Visibility
    el.btnToggleKeyVisibility.addEventListener('click', () => {
      if (el.currentApiKey.type === 'password') {
        el.currentApiKey.type = 'text';
        el.btnToggleKeyVisibility.textContent = '🔒';
      } else {
        el.currentApiKey.type = 'password';
        el.btnToggleKeyVisibility.textContent = '👁️';
      }
    });

    // Chip Category Tabs
    el.chipCategoryTabs.querySelectorAll('.chip-tab').forEach(tab => {
      tab.addEventListener('click', () => {
        el.chipCategoryTabs.querySelectorAll('.chip-tab').forEach(t => t.classList.remove('active'));
        tab.classList.add('active');
        state.activeCategory = tab.dataset.category;
        renderChips(state.activeCategory);
      });
    });

    // AI Prompt Enhance Button
    el.btnAiEnhancePrompt.addEventListener('click', async () => {
      const current = el.promptInput.value.trim();
      if (!current) {
        showToast('Type a prompt or idea first to enhance!', 'error');
        el.promptInput.focus();
        return;
      }

      const originalText = el.btnAiEnhancePrompt.innerHTML;
      el.btnAiEnhancePrompt.innerHTML = '<span class="magic-spark">⏳</span> Enhancing...';
      el.btnAiEnhancePrompt.disabled = true;

      try {
        const customKey = el.currentApiKey.value.trim();
        const style = state.mode === 'game' ? 'game_asset' : 'cinematic';
        const enhanced = await API.enhancePrompt(current, state.provider, customKey, style);
        if (enhanced) {
          el.promptInput.value = enhanced;
          showToast('Prompt enriched with AI lighting, depth & details!', 'success');
        }
      } catch (err) {
        showToast(err.message, 'error');
      } finally {
        el.btnAiEnhancePrompt.innerHTML = originalText;
        el.btnAiEnhancePrompt.disabled = false;
      }
    });

    // Aspect Ratio Buttons
    el.aspectBtns.forEach(btn => {
      btn.addEventListener('click', () => {
        el.aspectBtns.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        state.selectedAspect = btn.dataset.aspect;
      });
    });

    // Model dropdown change
    el.modelSelect.addEventListener('change', (e) => {
      state.selectedModel = e.target.value;
    });

    // Generate Button
    el.btnGenerate.addEventListener('click', handleGenerate);

    // View Modes
    el.btnViewOriginal.addEventListener('click', () => switchToViewMode('original'));
    el.btnViewTransparent.addEventListener('click', () => switchToViewMode('transparent'));

    // Manual Background Removal Button
    el.btnManualRemoveBg.addEventListener('click', async () => {
      if (!state.currentGeneration) return;
      el.btnManualRemoveBg.disabled = true;
      el.btnManualRemoveBg.textContent = '⏳ Extracting...';

      try {
        const updated = await API.removeBackground(state.currentGeneration.id);
        loadGenerationIntoStage(updated);
        switchToViewMode('transparent');
        showToast('Background removed cleanly! Transparent PNG ready.', 'success');
      } catch (err) {
        showToast(err.message, 'error');
        el.btnManualRemoveBg.disabled = false;
        el.btnManualRemoveBg.textContent = '🪄 Extract Alpha';
      }
    });

    // Copy Prompt
    el.btnCopyPrompt.addEventListener('click', () => {
      if (!state.currentGeneration) return;
      navigator.clipboard.writeText(state.currentGeneration.prompt);
      showToast('Prompt copied to clipboard!', 'success');
    });

    // Key Modal Management
    const openModal = () => el.keyModal.classList.remove('hidden');
    const closeModal = () => el.keyModal.classList.add('hidden');

    el.btnOpenKeyModal.addEventListener('click', openModal);
    el.keyStatusBadge.addEventListener('click', openModal);
    el.btnCloseKeyModal.addEventListener('click', closeModal);
    el.btnDoneKeyModal.addEventListener('click', closeModal);

    el.btnSaveOpenAiModal.addEventListener('click', async () => {
      const key = el.modalOpenAiKey.value.trim();
      if (!key) return showToast('Enter OpenAI key first', 'error');
      try {
        await API.saveApiKey('openai', key);
        showToast('OpenAI key saved to .env', 'success');
        el.modalOpenAiKey.value = '';
        await refreshKeyStatus();
        if (state.provider === 'openai') await syncProviderModels(false);
      } catch (err) {
        showToast(err.message, 'error');
      }
    });

    el.btnSaveGeminiModal.addEventListener('click', async () => {
      const key = el.modalGeminiKey.value.trim();
      if (!key) return showToast('Enter Gemini key first', 'error');
      try {
        await API.saveApiKey('gemini', key);
        showToast('Gemini key saved to .env', 'success');
        el.modalGeminiKey.value = '';
        await refreshKeyStatus();
        if (state.provider === 'gemini') await syncProviderModels(false);
      } catch (err) {
        showToast(err.message, 'error');
      }
    });
  }

  // Start
  init();
});
