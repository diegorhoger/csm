import React, { useState, useEffect } from 'react';
import { VoiceOptions } from '../../services/ttsService';

interface VoiceCustomizationControlsProps {
  onVoiceOptionsChange: (options: VoiceOptions) => void;
  initialOptions?: VoiceOptions;
  isExpanded: boolean;
  onToggle: () => void;
}

const VoiceCustomizationControls: React.FC<VoiceCustomizationControlsProps> = ({
  onVoiceOptionsChange,
  initialOptions,
  isExpanded,
  onToggle,
}) => {
  // Initialize state with default values or provided initial options
  const [speed, setSpeed] = useState(initialOptions?.speed || 1.0);
  const [stability, setStability] = useState(initialOptions?.stability || 0.5);
  const [similarityBoost, setSimilarityBoost] = useState(initialOptions?.similarityBoost || 0.75);
  const [style, setStyle] = useState(initialOptions?.style || 0.0);

  // Update parent component when options change
  useEffect(() => {
    onVoiceOptionsChange({
      speed,
      stability,
      similarityBoost,
      style,
    });
  }, [speed, stability, similarityBoost, style, onVoiceOptionsChange]);

  // Format value as percentage or decimal
  const formatValue = (value: number, isPercentage = false) => {
    return isPercentage 
      ? `${Math.round(value * 100)}%`
      : value.toFixed(1);
  };

  return (
    <div className="voice-customization-controls bg-gray-50 rounded-md p-3 mb-3 border border-gray-200">
      <div className="flex justify-between items-center mb-2">
        <h3 className="text-sm font-medium">Voice Settings</h3>
        <button 
          onClick={onToggle}
          className="text-xs px-2 py-1 bg-gray-200 rounded hover:bg-gray-300 transition-colors"
        >
          {isExpanded ? 'Hide' : 'Show'}
        </button>
      </div>

      {isExpanded && (
        <div className="controls-container space-y-3">
          <div className="control-group">
            <label htmlFor="speed-slider" className="flex justify-between text-xs mb-1">
              <span>Speed: {formatValue(speed)}</span>
            </label>
            <input
              id="speed-slider"
              type="range"
              min="0.5"
              max="2.0"
              step="0.1"
              value={speed}
              onChange={(e) => setSpeed(parseFloat(e.target.value))}
              className="w-full h-2 rounded-lg appearance-none cursor-pointer bg-gray-300"
              aria-valuetext={`Speed: ${formatValue(speed)}`}
            />
            <p className="text-xs text-gray-500 mt-1">Adjusts how quickly the voice speaks</p>
          </div>

          <div className="control-group">
            <label htmlFor="stability-slider" className="flex justify-between text-xs mb-1">
              <span>Stability: {formatValue(stability, true)}</span>
            </label>
            <input
              id="stability-slider"
              type="range"
              min="0.0"
              max="1.0"
              step="0.05"
              value={stability}
              onChange={(e) => setStability(parseFloat(e.target.value))}
              className="w-full h-2 rounded-lg appearance-none cursor-pointer bg-gray-300"
              aria-valuetext={`Stability: ${formatValue(stability, true)}`}
            />
            <p className="text-xs text-gray-500 mt-1">Higher values make voice more stable/consistent</p>
          </div>

          <div className="control-group">
            <label htmlFor="similarity-slider" className="flex justify-between text-xs mb-1">
              <span>Voice Clarity: {formatValue(similarityBoost, true)}</span>
            </label>
            <input
              id="similarity-slider"
              type="range"
              min="0.0"
              max="1.0"
              step="0.05"
              value={similarityBoost}
              onChange={(e) => setSimilarityBoost(parseFloat(e.target.value))}
              className="w-full h-2 rounded-lg appearance-none cursor-pointer bg-gray-300"
              aria-valuetext={`Voice Clarity: ${formatValue(similarityBoost, true)}`}
            />
            <p className="text-xs text-gray-500 mt-1">Higher values enhance voice clarity</p>
          </div>

          <div className="control-group">
            <label htmlFor="style-slider" className="flex justify-between text-xs mb-1">
              <span>Style Intensity: {formatValue(style, true)}</span>
            </label>
            <input
              id="style-slider"
              type="range"
              min="0.0"
              max="1.0"
              step="0.05"
              value={style}
              onChange={(e) => setStyle(parseFloat(e.target.value))}
              className="w-full h-2 rounded-lg appearance-none cursor-pointer bg-gray-300"
              aria-valuetext={`Style Intensity: ${formatValue(style, true)}`}
            />
            <p className="text-xs text-gray-500 mt-1">Controls the expressiveness of the voice</p>
          </div>

          <div className="flex justify-end mt-2">
            <button
              onClick={() => {
                // Reset to defaults
                setSpeed(1.0);
                setStability(0.5);
                setSimilarityBoost(0.75);
                setStyle(0.0);
              }}
              className="text-xs px-2 py-1 bg-gray-200 rounded hover:bg-gray-300 transition-colors"
            >
              Reset to Default
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default VoiceCustomizationControls; 