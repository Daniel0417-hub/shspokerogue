from pathlib import Path

ROOT = Path('pokerogue')

def replace_once(path: str, old: str, new: str):
    p = ROOT / path
    s = p.read_text()
    if new in s:
        return
    if old not in s:
        raise RuntimeError(f'Patch anchor not found: {path}: {old[:100]!r}')
    p.write_text(s.replace(old, new, 1))

# Add the cheat UI mode.
replace_once(
    'src/enums/ui-mode.ts',
    '  SETTINGS_KEYBOARD,\n',
    '  SETTINGS_KEYBOARD,\n  SETTINGS_CHEATS,\n',
)

# Add the cheat tab to every settings handler's shared tab strip.
replace_once(
    'src/ui/settings/base-settings-ui-handler.ts',
    '    { mode: UiMode.SETTINGS_KEYBOARD, labelKey: "settings:keyboard" },\n',
    '    { mode: UiMode.SETTINGS_KEYBOARD, labelKey: "settings:keyboard" },\n    { mode: UiMode.SETTINGS_CHEATS, labelKey: "CHEATS" },\n',
)

# Add the custom handler import and registration.
replace_once(
    'src/ui/ui.ts',
    'import { GeneralSettingsUiHandler } from "#ui/general-settings-ui-handler";\n',
    'import { GeneralSettingsUiHandler } from "#ui/general-settings-ui-handler";\nimport { CheatSettingsUiHandler } from "#ui/cheat-settings-ui-handler";\n',
)
replace_once(
    'src/ui/ui.ts',
    '      new SettingsKeyboardUiHandler(),\n',
    '      new SettingsKeyboardUiHandler(),\n      new CheatSettingsUiHandler(),\n',
)

# Settings modes should not use the normal screen transition.
replace_once(
    'src/ui/ui.ts',
    '  UiMode.SETTINGS_KEYBOARD,\n',
    '  UiMode.SETTINGS_KEYBOARD,\n  UiMode.SETTINGS_CHEATS,\n',
)

# Add the actual cheat handler. It reuses the existing settings UI and local-save system.
handler = r'''import { globalScene } from "#app/global-scene";
import { AbilityAttr } from "#enums/ability-attr";
import { DexAttr } from "#enums/dex-attr";
import { Nature } from "#enums/nature";
import { UiMode } from "#enums/ui-mode";
import { speciesDataRegistry } from "#app/global-species-data-registry";
import type { SettingsUiItem } from "#types/settings";
import { BaseSettingsUiHandler } from "#ui/base-settings-ui-handler";

const CHEAT_KEYS = {
  dex: "pokerogue_cheat_dex",
  ability: "pokerogue_cheat_ability",
  passive: "pokerogue_cheat_passive",
  eggMoves: "pokerogue_cheat_egg_moves",
  nature: "pokerogue_cheat_nature",
} as const;

type CheatKey = keyof typeof CHEAT_KEYS;

const items: SettingsUiItem[] = [
  { key: "dexForDevs", label: "도감 등록", options: [{ value: false, label: "OFF" }, { value: true, label: "ON" }] },
  { key: "dexForDevs", label: "특성", options: [{ value: false, label: "OFF" }, { value: true, label: "ON" }] },
  { key: "dexForDevs", label: "패시브", options: [{ value: false, label: "OFF" }, { value: true, label: "ON" }] },
  { key: "dexForDevs", label: "알 기술", options: [{ value: false, label: "OFF" }, { value: true, label: "ON" }] },
  { key: "dexForDevs", label: "성격", options: [{ value: false, label: "OFF" }, { value: true, label: "ON" }] },
];

export class CheatSettingsUiHandler extends BaseSettingsUiHandler {
  private readonly cheatKeys: CheatKey[] = ["dex", "ability", "passive", "eggMoves", "nature"];

  constructor() {
    // The base settings renderer expects a real settings category. We override save/show
    // behavior, so the existing general setting is never modified.
    super("general", items);
  }

  public override show(args: any[]): boolean {
    const result = super.show(args);
    this.cheatKeys.forEach((key, i) => {
      const enabled = localStorage.getItem(CHEAT_KEYS[key]) === "1";
      this.setOptionCursor(i, enabled ? 1 : 0, false);
    });
    return result;
  }

  protected override handleSaveSetting(uiItem: SettingsUiItem, newValue: boolean): void {
    const index = this.uiItems.indexOf(uiItem);
    const key = this.cheatKeys[index];
    if (!key) {
      return;
    }

    if (!newValue) {
      // Unlocks are intentionally not revoked: turning a cheat off only stops re-applying it.
      localStorage.removeItem(CHEAT_KEYS[key]);
      return;
    }

    localStorage.setItem(CHEAT_KEYS[key], "1");
    this.applyCheat(key);
  }

  private applyCheat(key: CheatKey): void {
    const gameData = globalScene.gameData;
    if (!gameData) {
      return;
    }

    const starters = speciesDataRegistry.getAllStarters();
    const allDexAttrs =
      DexAttr.NON_SHINY
      | DexAttr.SHINY
      | DexAttr.MALE
      | DexAttr.FEMALE
      | DexAttr.DEFAULT_VARIANT
      | DexAttr.VARIANT_2
      | DexAttr.VARIANT_3
      | DexAttr.DEFAULT_FORM;
    const allNatures = Math.pow(2, Object.values(Nature).filter(v => typeof v === "number").length) - 1;

    for (const speciesId of starters) {
      const dex = gameData.dexData[speciesId];
      if (dex) {
        if (key === "dex") {
          dex.seenAttr |= allDexAttrs;
          dex.caughtAttr |= allDexAttrs;
          dex.seenCount = Math.max(dex.seenCount, 1);
          dex.caughtCount = Math.max(dex.caughtCount, 1);
        }
        if (key === "nature") {
          dex.natureAttr |= allNatures;
        }
      }

      const starter = gameData.starterData[speciesId];
      if (!starter) {
        continue;
      }
      if (key === "ability") {
        starter.abilityAttr |= AbilityAttr.ABILITY_1 | AbilityAttr.ABILITY_2 | AbilityAttr.ABILITY_HIDDEN;
      }
      if (key === "passive") {
        starter.passiveAttr |= 1;
      }
      if (key === "eggMoves") {
        starter.eggMoves |= 0b1111;
      }
    }

    void gameData.saveSystem();
  }
}
'''
(ROOT / 'src/ui/cheat-settings-ui-handler.ts').write_text(handler)
