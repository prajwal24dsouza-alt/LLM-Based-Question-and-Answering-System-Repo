/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#08111f",
        panel: "#0f1b31",
        mist: "#9fb2cb",
        glow: "#56e0c5",
        ember: "#ff8d5c",
        sky: "#78a9ff",
      },
      boxShadow: {
        halo: "0 20px 60px rgba(6, 14, 28, 0.45)",
      },
      backgroundImage: {
        "mesh-glow":
          "radial-gradient(circle at top left, rgba(120,169,255,0.20), transparent 30%), radial-gradient(circle at top right, rgba(255,141,92,0.16), transparent 28%), radial-gradient(circle at bottom, rgba(86,224,197,0.18), transparent 38%)",
      },
      fontFamily: {
        display: ["Space Grotesk", "Segoe UI", "sans-serif"],
        body: ["Manrope", "Segoe UI", "sans-serif"],
      },
    },
  },
  plugins: [],
};
