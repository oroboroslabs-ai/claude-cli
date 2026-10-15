import io, sys
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
p = Path(r"Q:\claude-cli\better-clawd-src\src\utils\theme.ts")
t = p.read_text(encoding="utf-8")

# 1) register the theme name
t = t.replace(
    "  'light-ansi',\n  'dark-ansi',\n] as const",
    "  'light-ansi',\n  'dark-ansi',\n  'oroboros-mono',\n] as const",
)

# 2) add the mono (black & white) theme right before getTheme
MONO = '''
/**
 * Oroboros mono — pure black & white (night sky). A selectable alternative to
 * the red-orange default. Grayscale only; no hue anywhere.
 */
const oroborosMonoTheme: Theme = {
  ...darkTheme,
  autoAccept: 'rgb(255,255,255)',
  bashBorder: 'rgb(180,180,180)',
  claude: 'rgb(255,255,255)',
  claudeShimmer: 'rgb(200,200,200)',
  claudeBlue_FOR_SYSTEM_SPINNER: 'rgb(220,220,220)',
  claudeBlueShimmer_FOR_SYSTEM_SPINNER: 'rgb(245,245,245)',
  permission: 'rgb(230,230,230)',
  permissionShimmer: 'rgb(255,255,255)',
  planMode: 'rgb(160,160,160)',
  ide: 'rgb(210,210,210)',
  promptBorder: 'rgb(120,120,120)',
  promptBorderShimmer: 'rgb(170,170,170)',
  text: 'rgb(255,255,255)',
  inverseText: 'rgb(0,0,0)',
  inactive: 'rgb(130,130,130)',
  inactiveShimmer: 'rgb(180,180,180)',
  subtle: 'rgb(70,70,70)',
  suggestion: 'rgb(230,230,230)',
  remember: 'rgb(230,230,230)',
  background: 'rgb(0,0,0)',
  success: 'rgb(235,235,235)',
  error: 'rgb(255,255,255)',
  warning: 'rgb(200,200,200)',
  merged: 'rgb(240,240,240)',
  warningShimmer: 'rgb(255,255,255)',
  diffAdded: 'rgb(40,40,40)',
  diffRemoved: 'rgb(20,20,20)',
  diffAddedDimmed: 'rgb(60,60,60)',
  diffRemovedDimmed: 'rgb(35,35,35)',
  diffAddedWord: 'rgb(210,210,210)',
  diffRemovedWord: 'rgb(130,130,130)',
  red_FOR_SUBAGENTS_ONLY: 'rgb(210,210,210)',
  blue_FOR_SUBAGENTS_ONLY: 'rgb(190,190,190)',
  green_FOR_SUBAGENTS_ONLY: 'rgb(170,170,170)',
  yellow_FOR_SUBAGENTS_ONLY: 'rgb(230,230,230)',
  purple_FOR_SUBAGENTS_ONLY: 'rgb(150,150,150)',
  orange_FOR_SUBAGENTS_ONLY: 'rgb(255,255,255)',
  pink_FOR_SUBAGENTS_ONLY: 'rgb(200,200,200)',
  cyan_FOR_SUBAGENTS_ONLY: 'rgb(120,120,120)',
  professionalBlue: 'rgb(200,200,200)',
  chromeYellow: 'rgb(255,255,255)',
  clawd_body: 'rgb(255,255,255)',
  clawd_background: 'rgb(0,0,0)',
  userMessageBackground: 'rgb(20,20,20)',
  userMessageBackgroundHover: 'rgb(36,36,36)',
  messageActionsBackground: 'rgb(22,22,22)',
  selectionBg: 'rgb(60,60,60)',
  bashMessageBackgroundColor: 'rgb(26,26,26)',
  memoryBackgroundColor: 'rgb(24,24,24)',
  rate_limit_fill: 'rgb(230,230,230)',
  rate_limit_empty: 'rgb(70,70,70)',
  fastMode: 'rgb(255,255,255)',
  fastModeShimmer: 'rgb(210,210,210)',
  briefLabelYou: 'rgb(210,210,210)',
  briefLabelClaude: 'rgb(255,255,255)',
  rainbow_red: 'rgb(255,255,255)',
  rainbow_orange: 'rgb(230,230,230)',
  rainbow_yellow: 'rgb(245,245,245)',
  rainbow_green: 'rgb(210,210,210)',
  rainbow_blue: 'rgb(190,190,190)',
  rainbow_indigo: 'rgb(170,170,170)',
  rainbow_violet: 'rgb(150,150,150)',
  rainbow_red_shimmer: 'rgb(255,255,255)',
  rainbow_orange_shimmer: 'rgb(245,245,245)',
  rainbow_yellow_shimmer: 'rgb(255,255,255)',
  rainbow_green_shimmer: 'rgb(230,230,230)',
  rainbow_blue_shimmer: 'rgb(215,215,215)',
  rainbow_indigo_shimmer: 'rgb(200,200,200)',
  rainbow_violet_shimmer: 'rgb(185,185,185)',
}

export function getTheme(themeName: ThemeName): Theme {'''
t = t.replace("\nexport function getTheme(themeName: ThemeName): Theme {", MONO, 1)

# 3) resolve the theme
t = t.replace(
    "    case 'dark-daltonized':\n      return darkDaltonizedTheme",
    "    case 'dark-daltonized':\n      return darkDaltonizedTheme\n    case 'oroboros-mono':\n      return oroborosMonoTheme",
)

p.write_text(t, encoding="utf-8")
print("oroboros-mono theme added:", 'oroboros-mono' in t, "| getTheme case:", "oroborosMonoTheme" in t)
