module.exports = {
  extends: [
    'react-app',
    'react-app/jest'
  ],
  rules: {
    // Prettier 관련 규칙 모두 비활성화
    'prettier/prettier': 'off',
    
    // 자주 걸리는 규칙들 완화
    'no-unused-vars': 'warn',
    'no-console': 'warn',
    'react-hooks/exhaustive-deps': 'warn',
    
    // 완전히 비활성화할 규칙들
    'no-undef': 'off',
    'jsx-a11y/anchor-is-valid': 'off',
    'jsx-a11y/click-events-have-key-events': 'off',
    'jsx-a11y/no-noninteractive-element-interactions': 'off',
    
    // 코드 스타일 관련 규칙들 비활성화
    'indent': 'off',
    'quotes': 'off',
    'semi': 'off',
    'comma-dangle': 'off',
    'object-curly-spacing': 'off',
    'array-bracket-spacing': 'off',
    'space-before-blocks': 'off',
    'keyword-spacing': 'off',
    'space-infix-ops': 'off'
  },
  env: {
    browser: true,
    es6: true,
    node: true,
    jest: true
  }
};