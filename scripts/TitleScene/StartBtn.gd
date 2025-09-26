extends Button

var next_scene = preload("res://scenes/Level_1.tscn")

func _on_pressed() -> void:
	var game_state: GameState = get_node("/root/GameState")
	game_state.init_level_state()
	get_tree().change_scene_to_packed(next_scene)
