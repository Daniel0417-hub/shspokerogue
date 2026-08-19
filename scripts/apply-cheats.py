from pathlib import Path

ROOT = Path('pokerogue')

def replace_once(path: str, old: str, new: str):
    p = ROOT / path
    s = p.read_text()
    if new in s:
        return
    if old not in s:
        raise RuntimeError(f'Patch anchor not found: {path}: {old[:120]!r}')
    p.write_text(s.replace(old, new, 1))

# Add five personal cheat toggles to the existing General Settings screen.
# They are deliberately handled by the custom handler below, so they never touch
# the normal settings manager or the server account system.
replace_once(
    'src/ui/settings/settings-ui-items.ts',
    '  {\n    key: "preferBatonPass",\n    label: t("settings:preferBatonPass"),\n    options: useOnOffOptions(),\n  },\n];',
    '''  {
    key: "preferBatonPass",
    label: t("settings:preferBatonPass"),
    options: useOnOffOptions(),
  },
];

// Personal local-save cheats. The keys are intercepted by GeneralSettingsUiHandler
// and therefore are not persisted through the normal SettingsManager.
(generalSettingsUiItems as SettingsUiItem[]).push(
  { key: "__cheat_dex", label: "치트: 도감 등록", options: useOnOffOptions() },
  { key: "__cheat_ability", label: "치트: 특성", options: useOnOffOptions() },
  { key: "__cheat_passive", label: "치트: 패시브", options: useOnOffOptions() },
  { key: "__cheat_egg_moves", label: "치트: 알 기술", options: useOnOffOptions() },
  { key: "__cheat_nature", label: "치트: 성격", options: useOnOffOptions() },
);'''
)

# Import the save-data enums and add the cheat implementation to the existing,
# well-tested GeneralSettingsUiHandler instead of introducing a second settings mode.
replace_once(
    'src/ui/settings/general-settings-ui-handler.ts',
    'import { eventBus } from "#app/event-bus";\n',
    '''import { eventBus } from "#app/event-bus";
import { globalScene } from "#app/global-scene";
import { AbilityAttr } from "#enums/ability-attr";
import { DexAttr } from "#enums/dex-attr";
import { Nature } from "#enums/nature";
import { speciesDataRegistry } from "#app/global-species-data-registry";
'''
)
# Remove the duplicate globalScene import introduced by the original import list.
replace_once(
    'src/ui/settings/general-settings-ui-handler.ts',
    'import { globalScene } from "#app/global-scene";\nimport type { GeneralSettingsKey, SettingsUiItem }',
    'import type { GeneralSettingsKey, SettingsUiItem }'
)

replace_once(
    'src/ui/settings/general-settings-ui-handler.ts',
    '  protected override handleSaveSetting<V = any>(uiItem: SettingsUiItem<GeneralSettingsKey>, newValue: V): void {\n',
    '''  protected override handleSaveSetting<V = any>(uiItem: SettingsUiItem<GeneralSettingsKey>, newValue: V): void {
    const cheatKey = String(uiItem.key);
    if (cheatKey.startsWith("__cheat_")) {
      if (newValue === true) {
        this.applyLocalCheat(cheatKey);
      }
      return;
    }
'''
)

# Insert the cheat application method before the existing resize helper.
replace_once(
    'src/ui/settings/general-settings-ui-handler.ts',
    '  private updateMoveTouchControlsSettingsLabel(): void {\n',
    '''  private applyLocalCheat(key: string): void {
    const gameData = globalScene.gameData;
    if (!gameData) {
      return;
    }

    // Use the actual save arrays/maps rather than a hard-coded species list.
    const speciesIds = Object.keys(gameData.starterData).map(Number);
    const allDexAttrs =
      DexAttr.NON_SHINY
      | DexAttr.SHINY
      | DexAttr.MALE
      | DexAttr.FEMALE
      | DexAttr.DEFAULT_VARIANT
      | DexAttr.VARIANT_2
      | DexAttr.VARIANT_3
      | DexAttr.DEFAULT_FORM;

    // Nature is represented as one bit per nature in DexEntry.natureAttr.
    const natureCount = Object.values(Nature).filter(value => typeof value === "number").length;
    const allNatureAttrs = (1 << natureCount) - 1;

    for (const speciesId of speciesIds) {
      const dex = gameData.dexData[speciesId];
      const starter = gameData.starterData[speciesId];

      if (key === "__cheat_dex" && dex) {
        dex.seenAttr |= allDexAttrs;
        dex.caughtAttr |= allDexAttrs;
        dex.seenCount = Math.max(dex.seenCount, 1);
        dex.caughtCount = Math.max(dex.caughtCount, 1);
      }

      if (key === "__cheat_nature" && dex) {
        dex.natureAttr |= allNatureAttrs;
      }

      if (!starter) {
        continue;
      }

      if (key === "__cheat_ability") {
        starter.abilityAttr |= AbilityAttr.ABILITY_1 | AbilityAttr.ABILITY_2 | AbilityAttr.ABILITY_HIDDEN;
      }

      if (key === "__cheat_passive") {
        // Passive unlock is represented by the starter's passive attribute.
        starter.passiveAttr |= 1;
      }

      if (key === "__cheat_egg_moves") {
        // Four egg-move unlock bits.
        starter.eggMoves |= 0b1111;
      }
    }

    void gameData.saveSystem();
  }

  private updateMoveTouchControlsSettingsLabel(): void {
'''
)

# Remove unused imports if the official beta already exposes them through a different path.
# The build itself will fail loudly if the upstream API changes, preventing a broken Pages deploy.
