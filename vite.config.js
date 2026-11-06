import { defineConfig } from 'vite';
export default defineConfig({
 base: '/Bases-de-datos-Dataset-Videojuegos/',
 server: {proxy: {'/Bases-de-datos-Dataset-Videojuegos/api': {target:'http://127.0.0.1:8000',rewrite:path=>path.replace('/Bases-de-datos-Dataset-Videojuegos','')}}},
});
