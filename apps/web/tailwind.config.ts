import type { Config } from "tailwindcss";

// 农场水墨令牌：全站唯一色板。Tailwind 默认色名被重映射到这套令牌，
// 因此组件里的 slate-*/indigo-* 等类名渲染出来的是水墨色而非原色。
const paper = {
  50: "#faf7f2",
  100: "#f2efe9",
  200: "#ebe7e0",
  300: "#d6d0ba",
  400: "#b6b09c",
  500: "#757a6b",
  600: "#4a4d44",
  700: "#3e3f36",
  800: "#2a2b26",
  900: "#242421",
  950: "#1e1e1b",
};

const olive = {
  50: "#f0f3ec",
  100: "#e2e8d9",
  200: "#c8d3b8",
  300: "#a8ba90",
  400: "#879f7a",
  500: "#617a55",
  600: "#4e6344",
  700: "#3f5137",
  800: "#33412d",
  900: "#2a3625",
  950: "#161d13",
};

// 黛：次要信息色（知识网络/图谱边）
const dai = {
  50: "#eef3f5",
  100: "#dce7ea",
  200: "#b9cfd6",
  300: "#8fb0ba",
  400: "#6d94a1",
  500: "#5b7c8d",
  600: "#4a6675",
  700: "#3d5460",
  800: "#334650",
  900: "#2b3b43",
  950: "#172126",
};

// 朱砂：危险/错题/强调
const cinnabar = {
  50: "#f9edeb",
  100: "#f2dcd8",
  200: "#e8b4ac",
  300: "#dd8b80",
  400: "#d1685b",
  500: "#c44a3d",
  600: "#a83c30",
  700: "#8c3227",
  800: "#6f281f",
  900: "#5c211a",
  950: "#33120e",
};

// 赭：待审核/警示
const ochre = {
  50: "#f7f1e3",
  100: "#efe3c8",
  200: "#dfc794",
  300: "#cba863",
  400: "#bb9245",
  500: "#a87f35",
  600: "#8c682b",
  700: "#705324",
  800: "#5c4420",
  900: "#4d391c",
  950: "#2b1f0f",
};

const config: Config = {
  darkMode: "class",
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./lib/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: "#617a55",
        ink: "#2a2b26",
        muted: "#757a6b",
        paper,
        olive,
        dai,
        cinnabar,
        ochre,
        slate: paper,
        gray: paper,
        zinc: paper,
        neutral: paper,
        stone: paper,
        indigo: olive,
        violet: dai,
        purple: dai,
        cyan: dai,
        sky: dai,
        blue: olive,
        emerald: olive,
        green: olive,
        teal: olive,
        rose: cinnabar,
        red: cinnabar,
        orange: ochre,
        amber: ochre,
        yellow: ochre,
      },
      fontFamily: {
        sans: ["Noto Serif SC", "serif"],
        serif: ["Noto Serif SC", "serif"],
        title: ["ZCOOL XiaoWei", "Noto Serif SC", "serif"],
        display: ["ZCOOL XiaoWei", "Noto Serif SC", "serif"],
        body: ["Noto Serif SC", "serif"],
        "ui-sans": ["Noto Sans SC", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "ui-monospace", "SFMono-Regular", "Menlo", "Consolas", "monospace"],
      },
      animation: {
        'glow-pulse': 'glow 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'slide-up': 'slideUp 0.3s ease-out forwards',
        'fade-in': 'fadeIn 0.2s ease-out forwards',
      },
      keyframes: {
        glow: {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0.6' },
        },
        slideUp: {
          from: { opacity: '0', transform: 'translateY(10px)' },
          to: { opacity: '1', transform: 'translateY(0)' },
        },
        fadeIn: {
          from: { opacity: '0' },
          to: { opacity: '1' },
        }
      }
    },
  },
  plugins: [],
};

export default config;
