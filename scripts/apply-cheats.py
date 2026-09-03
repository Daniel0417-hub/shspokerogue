from pathlib import Path

ROOT = Path('pokerogue')


def replace_once(path: str, old: str, new: str):
    p = ROOT / path
    s = p.read_text()
    if new in s:
        return
    if old not in s:
        raise RuntimeError(f'Patch anchor not found: {path}: {old[:160]!r}')
    p.write_text(s.replace(old, new, 1))


# Add a dedicated Cheat Mode to the New Game menu. Cheat Mode is still a
# Classic run internally; the local flag is consumed only by SelectStarterPhase.
replace_once(
    'src/phases/title-phase.ts',
    '        handler: () => {\n          const setModeAndEnd = (gameMode: GameModes) => {\n            this.gameMode = gameMode;',
    '''        handler: () => {
          localStorage.setItem("pokerogue_cheat_mode", "0");
          const setModeAndEnd = (gameMode: GameModes, cheatMode = false) => {
            localStorage.setItem("pokerogue_cheat_mode", cheatMode ? "1" : "0");
            this.gameMode = gameMode;
            const finish = () => {
              globalScene.ui.setMode(UiMode.MESSAGE);
              globalScene.ui.clearText();
              this.end();
            };
            if (cheatMode) {
              finish();
            } else {
              // Reload the persisted system save so temporary Cheat Mode
              // unlocks are removed from memory before a normal run starts.
              globalScene.ui.setMode(UiMode.MESSAGE);
              void globalScene.gameData.loadSystem().then(finish);
            }'''
)

# Always expose Challenge and Endless, without requiring the normal Classic
# victory/unlock flag. Keep the normal Classic option and add Cheat Mode beside it.
replace_once(
    'src/phases/title-phase.ts',
    '''          options.push({
            label: GameMode.getModeName(GameModes.CLASSIC),
            handler: () => {
              localStorage.setItem("pokerogue_cheat_mode", "0");
              globalScene.ui.setMode(UiMode.MESSAGE);
              void globalScene.gameData.loadSystem().then(() => {
                setModeAndEnd(GameModes.CLASSIC);
              });
              return true;
            },
          });''',
    '''          options.push({
            label: GameMode.getModeName(GameModes.CLASSIC),
            handler: () => {
              setModeAndEnd(GameModes.CLASSIC);
              return true;
            },
          });
          options.push({
            label: "치트 모드 (클래식)",
            handler: () => {
              setModeAndEnd(GameModes.CLASSIC, true);
              return true;
            },
          });'''
)

# Remove the Classic-victory gate for Challenge/Endless in the New Game menu.
replace_once(
    'src/phases/title-phase.ts',
    '          if (gameData.isUnlocked(Unlockables.ENDLESS_MODE)) {',
    '          if (true) {'
)

# Prevent every later saveSystem() call during a Cheat Mode run from writing
# the temporary unlocked collection into the normal local system save.
replace_once(
    'src/system/game-data.ts',
    '''  public async saveSystem(): Promise<boolean> {
    const data = this.getSystemSaveData();''',
    '''  public async saveSystem(): Promise<boolean> {
    if (localStorage.getItem("pokerogue_cheat_mode") === "1") {
      globalScene.ui.savingIcon.hide();
      return true;
    }

    const data = this.getSystemSaveData();'''
)

# When Cheat Mode enters starter selection, unlock the full local collection:
# all species in the Dex, all abilities, all four egg-move slots, passive, and
# every Nature. Dex attributes are bigint in the upstream source.
replace_once(
    'src/phases/select-starter-phase.ts',
    'import { ChallengeType } from "#enums/challenge-type";\n',
    '''import { ChallengeType } from "#enums/challenge-type";
import { AbilityAttr } from "#enums/ability-attr";
import { DexAttr } from "#enums/dex-attr";
import { Nature } from "#enums/nature";
'''
)

replace_once(
    'src/phases/select-starter-phase.ts',
    '''  start() {
    super.start();

    audioManager.playBgm("menu");''',
    '''  start() {
    super.start();

    if (localStorage.getItem("pokerogue_cheat_mode") === "1") {
      this.activateCheatMode();
    }

    audioManager.playBgm("menu");'''
)

replace_once(
    'src/phases/select-starter-phase.ts',
    '''  /**
   * Initialize starters before starting the first battle
   * @param starters - Array of {@linkcode Starter}s with which to start the battle
   */''',
    '''  private activateCheatMode(): void {
    const { gameData } = globalScene;
    const allDexAttrs =
      DexAttr.NON_SHINY
      | DexAttr.SHINY
      | DexAttr.MALE
      | DexAttr.FEMALE
      | DexAttr.DEFAULT_VARIANT
      | DexAttr.VARIANT_2
      | DexAttr.VARIANT_3
      | DexAttr.DEFAULT_FORM;
    const allNatureAttrs = (2 ** Object.values(Nature).filter(value => typeof value === "number").length) - 1;

    for (const species of speciesDataRegistry.getAllSpecies()) {
      const dex = gameData.dexData[species.speciesId];
      const starter = gameData.starterData[species.speciesId];

      if (dex) {
        dex.seenAttr |= allDexAttrs;
        dex.caughtAttr |= allDexAttrs;
        dex.natureAttr = allNatureAttrs;
        dex.seenCount = Math.max(dex.seenCount, 1);
        dex.caughtCount = Math.max(dex.caughtCount, 1);
      }

      if (starter) {
        starter.abilityAttr |= AbilityAttr.ABILITY_1 | AbilityAttr.ABILITY_2 | AbilityAttr.ABILITY_HIDDEN;
        starter.passiveAttr |= 1;
        starter.eggMoves |= 0b1111;
      }
    }
  }

  /**
   * Initialize starters before starting the first battle
   * @param starters - Array of {@linkcode Starter}s with which to start the battle
   */'''
)
