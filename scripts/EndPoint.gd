extends Area2D


func _on_body_entered(body: Node2D) -> void:
	if body.is_in_group("player"):
		# Deferred: the level cannot be freed inside its own physics callback.
		get_tree().change_scene_to_file.call_deferred("res://scenes/FinishLevel.tscn")
