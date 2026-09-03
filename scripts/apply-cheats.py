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
            // A key/button event can reach this handler more than once.  Once
            // the mode is chosen, make TitlePhase.end() strictly one-shot so
            // duplicate SelectStarter/Encounter phases cannot be queued.
            if (this.gameMode != null) {
              return;
            }
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
              setModeAndEnd(GameModes.CLASSIC);
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

# TitlePhase is a transition boundary. If a duplicated input event or another
# stale callback reaches end() twice, discard phases queued by the previous
# invocation before constructing the one authoritative next sequence.
replace_once(
    'src/phases/title-phase.ts',
    '''  end(): void {
    if (!this.loaded && !globalScene.gameMode.isDaily) {''',
    '''  end(): void {
    // Starting a run must have exactly one next-phase sequence. This also
    // neutralizes a duplicate ENTER/SPACE-style input reaching end() twice.
    globalScene.phaseManager.clearPhaseQueue();

    if (!this.loaded && !globalScene.gameMode.isDaily) {'''
)

# If a duplicate SelectStarterPhase was already queued, the first real starter
# phase removes it. Only the current phase continues, so the same UI handler
# cannot be driven by two starter phases in sequence. The Cheat Mode activation
# is done here as well because this is the first phase of the new run.
replace_once(
    'src/phases/select-starter-phase.ts',
    '''  start() {
    super.start();

    audioManager.playBgm("menu");''',
    '''  start() {
    super.start();

    // There should only ever be one starter-selection phase in a new run.
    // Remove any stale duplicate left in the phase queue before showing the UI.
    globalScene.phaseManager.removeAllPhasesOfType("SelectStarterPhase");

    if (localStorage.getItem("pokerogue_cheat_mode") === "1") {
      this.activateCheatMode();
    }

    audioManager.playBgm("menu");'''
)

# This marker is intentionally a no-op. Cheat activation is already included in
# the SelectStarterPhase start patch above; keeping the check here makes the
# patch idempotent if this script is rerun against an already patched tree.
replace_once(
    'src/phases/select-starter-phase.ts',
    '''  start() {
    super.start();

    // There should only ever be one starter-selection phase in a new run.
    // Remove any stale duplicate left in the phase queue before showing the UI.
    globalScene.phaseManager.removeAllPhasesOfType("SelectStarterPhase");

    if (localStorage.getItem("pokerogue_cheat_mode") === "1") {
      this.activateCheatMode();
    }

    audioManager.playBgm("menu");''',
    '''  start() {
    super.start();

    // There should only ever be one starter-selection phase in a new run.
    // Remove any stale duplicate left in the phase queue before showing the UI.
    globalScene.phaseManager.removeAllPhasesOfType("SelectStarterPhase");

    if (localStorage.getItem("pokerogue_cheat_mode") === "1") {
      this.activateCheatMode();
    }

    audioManager.playBgm("menu");'''
)

# If the same UI handler is reused by a stale/duplicate phase, never carry the
# previous phase's selected Pokemon into the new starter-selection window.
replace_once(
    'src/ui/handlers/starter-select-ui-handler.ts',
    '''    if (args.length > 0 && args[0] instanceof Function) {
      super.show(args);
      this.starterSelectCallback = args[0] as StarterSelectCallback;''',
    '''    if (args.length > 0 && args[0] instanceof Function) {
      super.show(args);

      // A new SelectStarterPhase must begin with a fresh team. This is
      // defensive against stale/duplicate phase instances sharing this UI
      // handler singleton.
      this.partyStarters.length = 0;
      this.partyStarterIds.length = 0;
      this.starterCursorObjs?.forEach(cursor => cursor.setVisible(false));
      this.partyCursorObj?.setVisible(false);
      this.startCursorObj?.setVisible(false);

      this.starterSelectCallback = args[0] as StarterSelectCallback;'''
)

# If the starter-select screen is cancelled before a team is submitted,
# return directly to the title screen instead of entering the save-slot flow.
# Also clear the Cheat Mode flag so leaving the screen cannot affect later runs.
replace_once(
    'src/phases/select-starter-phase.ts',
    '''    globalScene.ui.setMode(UiMode.STARTER_SELECT, (starters: Starter[]) => {
      globalScene.ui.clearText();''',
    '''    globalScene.ui.setMode(UiMode.STARTER_SELECT, (starters: Starter[]) => {
      // An empty starter list is the cancel/back-out path from starter select.
      if (!starters || starters.length === 0) {
        localStorage.setItem("pokerogue_cheat_mode", "0");
        globalScene.phaseManager.toTitleScreen();
        this.end();
        return;
      }
      globalScene.ui.clearText();'''
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

# Import the enum objects used by the injected runtime code. These are not
# globals in the upstream module and must be imported explicitly.
replace_once(
    'src/phases/select-starter-phase.ts',
    'import { ChallengeType } from "#enums/challenge-type";\n',
    'import { AbilityAttr } from "#enums/ability-attr";\nimport { ChallengeType } from "#enums/challenge-type";\nimport { DexAttr } from "#enums/dex-attr";\n'
)

# When Cheat Mode enters starter selection, unlock the full local collection:
# all species in the Dex, all abilities, all four egg-move slots, passive, and
# every Nature. The current upstream Dex nature mask uses bigint values.
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
    let allNatureAttrs = 0n;
    for (let i = 0; i < 25; i++) {
      allNatureAttrs |= 1n << BigInt(i);
    }

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
