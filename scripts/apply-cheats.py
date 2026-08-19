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

replace_once(
    'src/ui/settings/settings-ui-items.ts',
    '  {\n    key: "preferBatonPass",\n    label: t("settings:preferBatonPass"),\n    options: useOnOffOptions(),\n  },\n];',
    '''  {
    key: "preferBatonPass",
    label: t("settings:preferBatonPass"),
    options: useOnOffOptions(),
  },
];

(generalSettingsUiItems as SettingsUiItem[]).push(
  { key: "__cheat_dex" as GeneralSettingsKey, label: "치트: 도감 등록", options: useOnOffOptions() },
  { key: "__cheat_ability" as GeneralSettingsKey, label: "치트: 특성", options: useOnOffOptions() },
  { key: "__cheat_passive" as GeneralSettingsKey, label: "치트: 패시브", options: useOnOffOptions() },
  { key: "__cheat_egg_moves" as GeneralSettingsKey, label: "치트: 알 기술", options: useOnOffOptions() },
  { key: "__cheat_nature" as GeneralSettingsKey, label: "치트: 성격", options: useOnOffOptions() },
);'''
)

replace_once(
    'src/ui/settings/general-settings-ui-handler.ts',
    'import { eventBus } from "#app/event-bus";\n',
    '''import { eventBus } from "#app/event-bus";
import { globalScene } from "#app/global-scene";
import { AbilityAttr } from "#enums/ability-attr";
import { DexAttr } from "#enums/dex-attr";
import { Nature } from "#enums/nature";
'''
)
replace_once(
    'src/ui/settings/general-settings-ui-handler.ts',
    'import { globalScene } from "#app/global-scene";\nimport type { GeneralSettingsKey, SettingsUiItem }',
    'import type { GeneralSettingsKey, SettingsUiItem }'
)

replace_once(
    'src/ui/settings/general-settings-ui-handler.ts',
    '  protected override handleSaveSetting<V = any>(uiItem: SettingsUiItem<GeneralSettingsKey>, newValue: V): void {\n',
    '''  public override show(args: any[]): boolean {
    const ret = super.show(args);
    const cheatKeys = ["__cheat_dex", "__cheat_ability", "__cheat_passive", "__cheat_egg_moves", "__cheat_nature"];
    cheatKeys.forEach((key, i) => {
      const row = this.uiItems.findIndex(item => String(item.key) === key);
      if (row >= 0) {
        this.setOptionCursor(row, localStorage.getItem(`pokerogue_${key}`) === "1" ? 1 : 0);
      }
    });
    return ret;
  }

  protected override handleSaveSetting<V = any>(uiItem: SettingsUiItem<GeneralSettingsKey>, newValue: V): void {
    const cheatKey = String(uiItem.key);
    if (cheatKey.startsWith("__cheat_")) {
      localStorage.setItem(`pokerogue_${cheatKey}`, newValue === true ? "1" : "0");
      if (newValue === true) {
        this.applyLocalCheat(cheatKey);
      }
      return;
    }
'''
)

replace_once(
    'src/ui/settings/general-settings-ui-handler.ts',
    '  private updateMoveTouchControlsSettingsLabel(): void {\n',
    '''  private applyLocalCheat(key: string): void {
    const gameData = globalScene.gameData;
    if (!gameData) {
      return;
    }

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
    const natureCount = Object.values(Nature).filter(value => typeof value === "number").length;
    const allNatureAttrs = (2 ** natureCount) - 1;

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
        starter.passiveAttr |= 1;
      }
      if (key === "__cheat_egg_moves") {
        starter.eggMoves |= 0b1111;
      }
    }

    void gameData.saveSystem();
  }

  private updateMoveTouchControlsSettingsLabel(): void {
'''
)
