extends Button

func _ready() -> void:
	grab_focus()

func _on_pressed() -> void:
	var current_level = 0
	if has_node("/root/GameState"):
		var game_state: GameState = get_node("/root/GameState")
		current_level = game_state.get_current_level()
		game_state.init_level_state()
	get_tree().change_scene_to_file("res://scenes/Level_" + str(current_level) + ".tscn")
