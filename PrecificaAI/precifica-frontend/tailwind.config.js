/** @type {import('tailwindcss').Config} */
export default {
    content: ["./index.html", "./src/**/*.{js,jsx}"],
    darkMode: "class",
    theme: {
        extend: {
            colors: {
                // Modified based on luxury request
                primary: "#ecb613", // Updated specific gold
                "primary-dark": "#b88d0f", // Darker shade for hovers if needed, keeping naming consistent if used elsewhere or inferring
                // Keeping existing structure but injecting requested values
                background: {
                    light: "#f8f8f6", // Updated
                    dark: "#221d10", // Updated
                },
                surface: {
                    light: "#FFFFFF",
                    dark: "#2A2620",
                },
                accent: {
                    rose: "#E8B4B8",
                    coral: "#FF6B6B",
                    yellow: "#FFD93D",
                },
            },
            fontFamily: {
                serif: ["Playfair Display", "Georgia", "serif"],
                display: ["Inter", "sans-serif"], // Updated to prioritize Inter as requested
                body: ["Inter", "system-ui", "sans-serif"],
                impact: ["Bebas Neue", "Impact", "sans-serif"],
            },
            borderRadius: {
                xl: "1.5rem", // Updated
                "2xl": "2rem", // Updated
            },
            boxShadow: {
                luxury: "0 4px 20px -2px rgba(236, 182, 19, 0.15)", // Updated to match primary
                soft: "0 4px 20px -2px rgba(0, 0, 0, 0.05)",
            },
        },
    },
    plugins: [],
};
