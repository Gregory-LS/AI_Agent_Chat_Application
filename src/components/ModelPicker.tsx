import React, { useState, useEffect } from 'react';

interface Model {
  id: string;
  name: string;
}

interface ModelPickerProps {
  onSelect: (model: Model) => void;
}

const ModelPicker: React.FC<ModelPickerProps> = ({ onSelect }) => {
  const [models, setModels] = useState<Model[]>([]);
  const [selectedModelId, setSelectedModelId] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchModels = async () => {
      try {
        const response = await fetch('/api/models');
        if (!response.ok) {
          throw new Error('Failed to fetch models');
        }
        const data: Model[] = await response.json();
        setModels(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error');
      } finally {
        setLoading(false);
      }
    };
    fetchModels();
  }, []);

  const handleSelectChange = (event: React.ChangeEvent<HTMLSelectElement>) => {
    const modelId = event.target.value;
    setSelectedModelId(modelId);
    const selectedModel = models.find((model) => model.id === modelId);
    if (selectedModel) {
      onSelect(selectedModel);
    }
  };

  if (loading) {
    return <div>Loading models...</div>;
  }

  if (error) {
    return <div>Error: {error}</div>;
  }

  return (
    <div>
      <label htmlFor="model-picker">Select Model:</label>
      <select
        id="model-picker"
        value={selectedModelId}
        onChange={handleSelectChange}
      >
        <option value="" disabled>
          -- Choose a model --
        </option>
        {models.map((model) => (
          <option key={model.id} value={model.id}>
            {model.name}
          </option>
        ))}
      </select>
    </div>
  );
};

export default ModelPicker;
