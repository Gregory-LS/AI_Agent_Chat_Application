import React, { useState, useEffect, useCallback } from 'react';
import PropTypes from 'prop-types';

/**
 * Debounced search input component.
 * Calls onChange with the trimmed value after a delay.
 */
const SearchInput = ({ placeholder, onSearch }) => {
  const [value, setValue] = useState('');

  const debouncedOnSearch = useCallback(
    debounce((term) => {
      onSearch(term);
    }, 300),
    [onSearch]
  );

  useEffect(() => {
    debouncedOnSearch(value);
    // cleanup
    return () => debouncedOnSearch.cancel && debouncedOnSearch.cancel();
  }, [value, debouncedOnSearch]);

  const handleChange = (e) => {
    setValue(e.target.value);
  };

  return (
    <div className="search-input-wrapper">
      <input
        type="text"
        className="search-input"
        placeholder={placeholder || 'Search conversations...'}
        value={value}
        onChange={handleChange}
        aria-label="Search conversations"
      />
    </div>
  );
};

SearchInput.propTypes = {
  placeholder: PropTypes.string,
  onSearch: PropTypes.func.isRequired,
};

/**
 * Simple debounce function (no external dependencies).
 */
function debounce(func, wait) {
  let timeout;
  const debouncedFn = (...args) => {
    clearTimeout(timeout);
    timeout = setTimeout(() => func(...args), wait);
  };
  debouncedFn.cancel = () => clearTimeout(timeout);
  return debouncedFn;
}

export default SearchInput;
