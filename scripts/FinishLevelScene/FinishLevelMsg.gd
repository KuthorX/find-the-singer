extends Node2D

func _ready():
	var time_label: Label = %TimeValue
	var letter_label: Label = %LettersValue
	var health_label: Label = %HealthValue

	if has_node("/root/GameState"):
		var game_state = get_node("/root/GameState")
		var elapsed_ms = game_state.get_elapsed_ms()
		var health = game_state.current_health
		var letters = game_state.letter_bonus_count
		
		var total_seconds = elapsed_ms / 1000
		var hours = total_seconds / 3600
		var minutes = (total_seconds % 3600) / 60
		var seconds = total_seconds % 60
		var milliseconds = elapsed_ms % 1000
		var time_string = "%02d:%02d:%02d.%03d" % [hours, minutes, seconds, milliseconds]
		time_label.text = time_string
		
		letter_label.text = str(letters)
		
		health_label.text = str(health)
