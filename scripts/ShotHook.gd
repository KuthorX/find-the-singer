extends Node

# Screenshot hook for headless web captures: index.html?shot=gameplay|finish|gameover
# jumps straight to that screen. Without the query parameter it does nothing.

const SCENES := {
	"gameplay": "res://scenes/Level_1.tscn",
	"finish": "res://scenes/FinishLevel.tscn",
	"gameover": "res://scenes/GameOver.tscn",
}

func _ready() -> void:
	if not OS.has_feature("web"):
		return
	var shot := str(JavaScriptBridge.eval("new URLSearchParams(location.search).get('shot') || ''"))
	if not SCENES.has(shot):
		return
	GameState.init_level_state()
	if shot == "finish":
		GameState.letter_bonus_count = 7
		GameState.set_elapsed_ms(83456)
	get_tree().change_scene_to_file.call_deferred(SCENES[shot])
