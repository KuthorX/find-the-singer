extends Button

var next_scene = preload("res://scenes/Level_1.tscn")

func _on_pressed() -> void:
	get_tree().change_scene_to_packed(next_scene)
