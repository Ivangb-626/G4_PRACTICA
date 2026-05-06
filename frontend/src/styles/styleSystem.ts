// Centralized Advanced Style System (Version 2.0)
export const Theme = {
    colors: {
        primary: '#00ffff',
        secondary: '#ffd700',
        danger: '#ff4444',
        ok: '#44ee44',
        bgGlass: 'rgba(7, 15, 36, 0.7)',
        bgDark: 'rgba(5, 10, 25, 0.9)',
        border: 'rgba(0, 255, 255, 0.4)',
        text: '#e0e0ff',
        textMuted: '#8888aa',
    },
    effects: {
        glass: 'blur(10px)',
        glow: '0 0 15px rgba(0, 255, 255, 0.3)',
        borderGradient: 'linear-gradient(135deg, rgba(0, 255, 255, 0.4), rgba(7, 15, 36, 0))'
    }
};

export const createPanelStyle = (active = false) => ({
    padding: '1.5rem',
    backgroundColor: Theme.colors.bgGlass,
    backdropFilter: Theme.effects.glass,
    border: `1px solid ${active ? Theme.colors.secondary : Theme.colors.border}`,
    borderRadius: '12px',
    boxShadow: '0 4px 15px rgba(0,0,0,0.5)',
    color: Theme.colors.text,
    fontFamily: 'monospace',
    transition: 'all 0.3s ease',
});

export const btnStyle = (hovered = false) => ({
    backgroundColor: hovered ? Theme.colors.primary : 'transparent',
    color: hovered ? '#000' : Theme.colors.primary,
    border: `1px solid ${Theme.colors.primary}`,
    padding: '0.6rem 1.2rem',
    cursor: 'pointer',
    fontWeight: 'bold' as const,
    textTransform: 'uppercase' as const,
    boxShadow: hovered ? Theme.effects.glow : 'none',
    transition: 'all 0.3s ease',
});
