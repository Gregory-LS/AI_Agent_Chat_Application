import React from 'react';
import styles from './ModelPicker.module.css';

interface ModelPickerProps {
  models: string[];
  selectedModel?: string;
  onSelect: (model: string) => void;
  disabled?: boolean;
  placeholder?: string;
}

const ModelPicker: React.FC<ModelPickerProps> = ({
  models,
  selectedModel,
  onSelect,
  disabled = false,
  placeholder = 'Select a model',
}) => {
  const handleChange = (event: React.ChangeEvent<HTMLSelectElement>) => {
    const value = event.target.value;
    if (value) {
      onSelect(value);
    }
  };

  return (
    <select
      className={styles.select}
      value={selectedModel || ''}
      onChange={handleChange}
      disabled={disabled}
      data-testid="model-picker"
    >
      <option value="" disabled>
        {placeholder}
      </option>
      {models.map((model) => (
        <option key={model} value={model}>
          {model}
        </option>
      ))}
    </select>
  );
};

export default ModelPicker;
