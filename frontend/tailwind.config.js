/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        bg:        '#111318',
        surface:   '#1C1E26',
        border:    '#2A2D38',
        primary:   '#1DB9E8',
        'primary-dim': '#1593BB',
        text:      '#E8EAF0',
        muted:     '#8B8FA8',
        success:   '#22C55E',
        warning:   '#F59E0B',
        danger:    '#EF4444',
      },
    },
  },
  plugins: [],
}
