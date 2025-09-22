extends Node

signal letter_bonus_collected(total_count)
signal health_changed(current_health, max_health)

var letter_bonus_count = 0
var max_health = 5
var current_health = max_health

# 每收集10封信件，血量上限增加1
const LETTERS_PER_HEALTH_UPGRADE = 10

func collect_letter_bonus():
	letter_bonus_count += 1
	emit_signal("letter_bonus_collected", letter_bonus_count)
	
	# 检查是否需要增加血量上限
	if letter_bonus_count % LETTERS_PER_HEALTH_UPGRADE == 0:
		max_health += 1
		current_health = max_health
		emit_signal("health_changed", current_health, max_health)

func take_damage(amount):
	current_health -= amount
	if current_health < 0:
		current_health = 0
	emit_signal("health_changed", current_health, max_health)
	
func heal(amount):
	current_health += amount
	if current_health > max_health:
		current_health = max_health
	emit_signal("health_changed", current_health, max_health)