import '@testing-library/jest-dom';

// Setup global test utilities
global.console = {
  ...console,
  error: jest.fn(), // Suppress console.error in tests
  warn: jest.fn(),  // Suppress console.warn in tests
};
