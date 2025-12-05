import { ValidationError } from './errors.js';

export function validateString(fieldName, value, options = {}) {
  if (typeof value !== 'string') {
    throw new ValidationError(`${fieldName} must be a string`);
  }
  
  const trimmed = value.trim();
  
  if (options.required && !trimmed) {
    throw new ValidationError(`${fieldName} is required`);
  }
  
  if (options.minLength && trimmed.length < options.minLength) {
    throw new ValidationError(`${fieldName} must be at least ${options.minLength} characters`);
  }
  
  if (options.maxLength && trimmed.length > options.maxLength) {
    throw new ValidationError(`${fieldName} must be at most ${options.maxLength} characters`);
  }
  
  return trimmed;
}

export function validateEnum(fieldName, value, allowedValues) {
  if (!allowedValues.includes(value)) {
    throw new ValidationError(
      `${fieldName} must be one of: ${allowedValues.join(', ')}`
    );
  }
  return value;
}

export function validateNumber(fieldName, value, options = {}) {
  const num = Number(value);
  
  if (isNaN(num)) {
    throw new ValidationError(`${fieldName} must be a number`);
  }
  
  if (options.min !== undefined && num < options.min) {
    throw new ValidationError(`${fieldName} must be at least ${options.min}`);
  }
  
  if (options.max !== undefined && num > options.max) {
    throw new ValidationError(`${fieldName} must be at most ${options.max}`);
  }
  
  return num;
}
