import React, { useEffect, useId, useMemo, useRef, useState } from 'react';
import { useModels } from '../hooks/useModels';
import type { Model } from '../types';
import './ModelPicker.css';

export interface ModelPickerProps {
  value?: string;
  onChange: (modelId: string) => void;
  models?: Model[];
  fetchModels?: () => Promise<Model[]>;
  disabled?: boolean;
  placeholder?: string;
  'aria-label'?: string;
  className?: string;
}

export function ModelPicker({
  value,
  onChange,
  models: providedModels,
  fetchModels: fetchModelsProp,
  disabled = false,
  placeholder = 'Select a model…',
  'aria-label': ariaLabel = 'Model picker',
  className,
}: ModelPickerProps) {
  const { models: fetchedModels, loading, error, retry } = useModels({
    fetchModels: fetchModelsProp,
    enabled: !providedModels,
  });

  const models = providedModels ?? fetchedModels;
  const listboxId = useId();

  const [isOpen, setIsOpen] = useState(false);
  const [query, setQuery] = useState('');
  const [activeIndex, setActiveIndex] = useState(-1);

  const containerRef = useRef<HTMLDivElement>(null);
  const listRef = useRef<HTMLUListElement>(null);
  const searchInputRef = useRef<HTMLInputElement>(null);

  const selectedModel = models.find((model) => model.id === value) ?? null;

  const filteredModels = useMemo(() => {
    const normalizedQuery = query.trim().toLowerCase();
    if (!normalizedQuery) {
      return models;
    }
    return models.filter((model) =>
      [model.id, model.name, model.description ?? '']
        .join(' ')
        .toLowerCase()
        .includes(normalizedQuery),
    );
  }, [models, query]);

  useEffect(() => {
    if (!isOpen) return;

    setQuery('');
    const selectedIndex = models.findIndex((model) => model.id === value);
    setActiveIndex(selectedIndex >= 0 ? selectedIndex : 0);

    const timeout = window.setTimeout(() => searchInputRef.current?.focus(), 0);
    return () => window.clearTimeout(timeout);
  }, [isOpen, models, value]);

  useEffect(() => {
    if (filteredModels.length === 0) {
      setActiveIndex(-1);
    } else if (activeIndex >= filteredModels.length) {
      setActiveIndex(filteredModels.length - 1);
    } else if (activeIndex === -1) {
      setActiveIndex(0);
    }
  }, [activeIndex, filteredModels.length]);

  useEffect(() => {
    if (!isOpen) return;

    const handlePointerDown = (event: MouseEvent | TouchEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handlePointerDown);
    document.addEventListener('touchstart', handlePointerDown);
    return () => {
      document.removeEventListener('mousedown', handlePointerDown);
      document.removeEventListener('touchstart', handlePointerDown);
    };
  }, [isOpen]);

  useEffect(() => {
    if (activeIndex < 0 || !listRef.current) return;
    const activeOption = listRef.current.querySelector<HTMLElement>('[data-active=true]');
    activeOption?.scrollIntoView({ block: 'nearest' });
  }, [activeIndex]);

  const toggleOpen = () => {
    if (disabled) return;
    setIsOpen((previous) => !previous);
  };

  const selectModel = (model: Model) => {
    onChange(model.id);
    setIsOpen(false);
  };

  const handleKeyDownOnTrigger = (event: React.KeyboardEvent<HTMLButtonElement>) => {
    if (event.key === 'ArrowDown') {
      event.preventDefault();
      setIsOpen(true);
    } else if (event.key === 'Escape') {
      setIsOpen(false);
    }
  };

  const handleKeyDown = (event: React.KeyboardEvent<HTMLInputElement>) => {
    if (filteredModels.length === 0) return;

    switch (event.key) {
      case 'Escape':
        setIsOpen(false);
        break;
      case 'ArrowDown':
        event.preventDefault();
        setActiveIndex((previous) => (previous + 1) % filteredModels.length);
        break;
      case 'ArrowUp':
        event.preventDefault();
        setActiveIndex((previous) => (previous - 1 + filteredModels.length) % filteredModels.length);
        break;
      case 'Home':
        event.preventDefault();
        setActiveIndex(0);
        break;
      case 'End':
        event.preventDefault();
        setActiveIndex(filteredModels.length - 1);
        break;
      case 'Enter':
        event.preventDefault();
        if (activeIndex >= 0 && activeIndex < filteredModels.length) {
          selectModel(filteredModels[activeIndex]);
        }
        break;
      case 'Tab':
        setIsOpen(false);
        break;
    }
  };

  return (
    <div
      ref={containerRef}
      className={className ? `model-picker ${className}` : 'model-picker'}
      data-testid='model-picker'
    >
      <button
        type='button'
        className='model-picker__trigger'
        aria-haspopup='listbox'
        aria-expanded={isOpen}
        aria-label={ariaLabel}
        disabled={disabled}
        onClick={toggleOpen}
        onKeyDown={handleKeyDownOnTrigger}
      >
        <span className='model-picker__selected'>
          {selectedModel ? selectedModel.name : placeholder}
        </span>
        <span className='model-picker__caret' aria-hidden='true'>
          ▾
        </span>
      </button>

      {isOpen && (
        <div className='model-picker__dropdown'>
          <input
            ref={searchInputRef}
            type='search'
            className='model-picker__search'
            placeholder='Search models…'
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            onKeyDown={handleKeyDown}
            aria-label='Search models'
            role='combobox'
            aria-expanded={isOpen}
            aria-haspopup='listbox'
            aria-autocomplete='list'
            aria-controls={listboxId}
            aria-activedescendant={
              activeIndex >= 0 && filteredModels[activeIndex]
                ? `model-option-${filteredModels[activeIndex].id}`
                : undefined
            }
          />
          {loading && <div className='model-picker__message'>Loading models…</div>}
          {error && (
            <div className='model-picker__message model-picker__error' role='alert'>
              {error}
              <button type='button' onClick={retry}>
                Retry
              </button>
            </div>
          )}
          {!loading && !error && filteredModels.length === 0 && (
            <div className='model-picker__message'>No models found.</div>
          )}
          {!loading && !error && filteredModels.length > 0 && (
            <ul
              ref={listRef}
              id={listboxId}
              className='model-picker__list'
              role='listbox'
              aria-label='Available models'
            >
              {filteredModels.map((model, index) => (
                <li
                  key={model.id}
                  id={`model-option-${model.id}`}
                  role='option'
                  aria-selected={model.id === value}
                  className={`model-picker__option${index === activeIndex ? ' model-picker__option--active' : ''}`}
                  data-active={index === activeIndex}
                  onClick={() => selectModel(model)}
                  onMouseEnter={() => setActiveIndex(index)}
                >
                  <div className='model-picker__option-name'>{model.name}</div>
                  {model.description && (
                    <div className='model-picker__option-description'>{model.description}</div>
                  )}
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}
