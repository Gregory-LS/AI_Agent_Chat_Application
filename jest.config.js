/** @type {import('jest').Config} */
module.exports = {
  preset: 'ts-jest',
  testEnvironment: 'jsdom',
  setupFilesAfterEnv: ['<rootDir>/src/setupTests.ts'],
  moduleNameMapper: {
    '(scss|sass|less|css)$': '<rootDir>/styleMock.js',
  },
  testMatch: ['<rootDir>/src/**/*.test.{ts,tsx}'],
};
