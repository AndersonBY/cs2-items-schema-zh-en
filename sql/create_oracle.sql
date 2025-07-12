
CREATE TABLE types (
	id SMALLINT NOT NULL, 
	name VARCHAR2(16 CHAR), 
	PRIMARY KEY (id)
)

;
CREATE TABLE origins (
	id SMALLINT NOT NULL, 
	name VARCHAR2(30 CHAR), 
	PRIMARY KEY (id)
)

;
CREATE TABLE qualities (
	id SMALLINT NOT NULL, 
	name VARCHAR2(16 CHAR), 
	name_zh VARCHAR2(32 CHAR), 
	PRIMARY KEY (id)
)

;
CREATE TABLE phases (
	id SMALLINT NOT NULL, 
	name VARCHAR2(16 CHAR), 
	PRIMARY KEY (id)
)

;
CREATE TABLE tints (
	id SMALLINT NOT NULL, 
	name VARCHAR2(16 CHAR), 
	name_zh VARCHAR2(32 CHAR), 
	PRIMARY KEY (id)
)

;
CREATE TABLE musics (
	id SMALLINT NOT NULL, 
	name VARCHAR2(16 CHAR), 
	name_zh VARCHAR2(32 CHAR), 
	PRIMARY KEY (id)
)

;
CREATE TABLE rarities (
	id SMALLINT NOT NULL, 
	character VARCHAR2(16 CHAR), 
	character_zh VARCHAR2(32 CHAR), 
	color VARCHAR2(16 CHAR) NOT NULL, 
	nonweapon VARCHAR2(16 CHAR) NOT NULL, 
	nonweapon_zh VARCHAR2(32 CHAR), 
	weapon VARCHAR2(16 CHAR) NOT NULL, 
	weapon_zh VARCHAR2(32 CHAR), 
	PRIMARY KEY (id)
)

;
CREATE TABLE wears (
	name VARCHAR2(30 CHAR) NOT NULL, 
	"from" FLOAT NOT NULL, 
	"to" FLOAT NOT NULL, 
	PRIMARY KEY (name)
)

;
CREATE TABLE definitions (
	defindex SMALLINT NOT NULL, 
	name VARCHAR2(60 CHAR) NOT NULL, 
	type SMALLINT NOT NULL, 
	quality SMALLINT, 
	rarity SMALLINT, 
	PRIMARY KEY (defindex), 
	FOREIGN KEY(type) REFERENCES types (id), 
	FOREIGN KEY(quality) REFERENCES qualities (id), 
	FOREIGN KEY(rarity) REFERENCES rarities (id)
)

;
CREATE TABLE paints (
	paintindex SMALLINT NOT NULL, 
	name VARCHAR2(60 CHAR) NOT NULL, 
	name_zh VARCHAR2(120 CHAR), 
	wear_min FLOAT NOT NULL, 
	wear_max FLOAT NOT NULL, 
	rarity SMALLINT NOT NULL, 
	phase SMALLINT, 
	PRIMARY KEY (paintindex), 
	FOREIGN KEY(rarity) REFERENCES rarities (id), 
	FOREIGN KEY(phase) REFERENCES phases (id)
)

;
CREATE TABLE sticker_kits (
	id SMALLINT NOT NULL, 
	name VARCHAR2(60 CHAR) NOT NULL, 
	name_zh VARCHAR2(120 CHAR), 
	rarity SMALLINT, 
	PRIMARY KEY (id), 
	FOREIGN KEY(rarity) REFERENCES rarities (id)
)

;
CREATE TABLE items (
	id VARCHAR2(16 CHAR) NOT NULL, 
	def SMALLINT NOT NULL, 
	paint SMALLINT, 
	image VARCHAR2(255 CHAR), 
	PRIMARY KEY (id), 
	CONSTRAINT uniq_paint_def UNIQUE (def, paint), 
	FOREIGN KEY(def) REFERENCES definitions (defindex), 
	FOREIGN KEY(paint) REFERENCES paints (paintindex)
)

;CREATE UNIQUE INDEX ix_paint_def ON items (def, paint);
CREATE TABLE containers (
	defindex SMALLINT NOT NULL, 
	associated SMALLINT, 
	"set" VARCHAR2(60 CHAR), 
	PRIMARY KEY (defindex), 
	FOREIGN KEY(defindex) REFERENCES items (id), 
	FOREIGN KEY(associated) REFERENCES items (id)
)

;
CREATE TABLE sticker_kit_containers (
	defindex SMALLINT NOT NULL, 
	PRIMARY KEY (defindex), 
	FOREIGN KEY(defindex) REFERENCES items (id)
)

;
CREATE TABLE music_kits (
	defindex SMALLINT NOT NULL, 
	PRIMARY KEY (defindex), 
	FOREIGN KEY(defindex) REFERENCES items (id)
)

;
CREATE TABLE items_containers (
	item VARCHAR2(16 CHAR) NOT NULL, 
	container SMALLINT NOT NULL, 
	PRIMARY KEY (item, container), 
	CONSTRAINT uniq_item_container UNIQUE (item, container), 
	FOREIGN KEY(item) REFERENCES items (id), 
	FOREIGN KEY(container) REFERENCES containers (defindex)
)

;CREATE UNIQUE INDEX idx_item_container ON items_containers (item, container);
CREATE TABLE musics_music_kits (
	music SMALLINT NOT NULL, 
	container SMALLINT NOT NULL, 
	PRIMARY KEY (music, container), 
	CONSTRAINT uniq_music_container UNIQUE (music, container), 
	FOREIGN KEY(music) REFERENCES musics (id), 
	FOREIGN KEY(container) REFERENCES music_kits (defindex)
)

;CREATE UNIQUE INDEX idx_music_container ON musics_music_kits (music, container);
CREATE TABLE sticker_kits_containers (
	kit SMALLINT NOT NULL, 
	container SMALLINT NOT NULL, 
	PRIMARY KEY (kit, container), 
	CONSTRAINT uniq_kit_container UNIQUE (kit, container), 
	FOREIGN KEY(kit) REFERENCES sticker_kits (id), 
	FOREIGN KEY(container) REFERENCES sticker_kit_containers (defindex)
)

;CREATE UNIQUE INDEX idx_kit_container ON sticker_kits_containers (kit, container);
