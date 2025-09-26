extends Node2D

func _ready():
	var container = get_node("CenterContainer/VBoxContainer")
	var level_label: Label = container.get_node("Level/Value")
	var time_label: Label = container.get_node("Time/Value")
	var letter_label: Label = container.get_node("HBoxContainer/Letter/Value")
	var health_label: Label = container.get_node("HBoxContainer/Health/Value")
	
	
	# 记录计时器启动时的毫秒时间
	if has_node("/root/GameState"):
		var game_state = get_node("/root/GameState")
		var elapsed_ms = game_state.get_elapsed_ms()
		var current_level = game_state.current_level
		var health = game_state.current_health
		var letters = game_state.letter_bonus_count
		
		level_label.text = str(current_level)
		
		var total_seconds = elapsed_ms / 1000
		var hours = total_seconds / 3600
		var minutes = (total_seconds % 3600) / 60
		var seconds = total_seconds % 60
		var milliseconds = elapsed_ms % 1000
		var time_string = "%02d:%02d:%02d.%03d" % [hours, minutes, seconds, milliseconds]
		time_label.text = time_string
		
		letter_label.text = str(letters)
		
		health_label.text = str(health)
		
		
