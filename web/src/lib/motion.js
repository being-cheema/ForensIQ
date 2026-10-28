import anime from 'animejs'

export const AN = anime
export const RM = () => !!(window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches)
export const canAnim = () => !!AN && !RM()
