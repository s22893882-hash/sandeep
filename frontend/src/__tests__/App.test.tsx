import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';

function App() {
  return (
    <div>
      <h1>Hello World</h1>
      <p>Welcome to the app</p>
    </div>
  );
}

describe('App Component', () => {
  it('renders without crashing', () => {
    render(<App />);
    expect(screen.getByText('Hello World')).toBeInTheDocument();
  });

  it('displays welcome message', () => {
    render(<App />);
    expect(screen.getByText('Welcome to the app')).toBeInTheDocument();
  });

  it('has correct structure', () => {
    const { container } = render(<App />);
    expect(container.querySelector('h1')).toBeTruthy();
    expect(container.querySelector('p')).toBeTruthy();
  });
});
