"""
CS2 Items Formatter Service
将所有CS2物品数据统一格式化为CS2Item结构
"""

import json
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass
class CS2Item:
    slug_name: str
    name: dict[str, str]
    description: dict[str, str]
    cover_image: str | None
    item_type: str
    weapon_defindex: int | None
    weapon_name: str | None
    paint_id: int | None
    item_id: int | None
    team: int | None
    model: str | None
    agent_name: dict[str, str]


class ItemFormatterService:
    def __init__(self, schemas_dir: str | Path = "schemas"):
        self.schemas_dir = Path(schemas_dir)
        self.type_mapping = {
            "Agent": "agent",
            "C4": "c4",
            "Graffiti": "graffiti",
            "Grenade": "grenade",
            "Key": "keychain",
            "Knife": "knife",
            "Machinegun": "weapon",
            "Mission": "mission",
            "Music Kit": "music_kit",
            "Pass": "pass",
            "Patch": "Patch",
            "Pistol": "weapon",
            "Campaign": "campaign",
            "Rifle": "weapon",
            "SMG": "weapon",
            "Shotgun": "weapon",
            "Sniper Rifle": "weapon",
            "Sticker": "sticker",
            "Tag": "tag",
            "Tool": "tool",
            "Charm": "charm",
            "Collectible": "collectible",
            "Container": "container",
            "Contract": "contract",
            "Equipment": "equipment",
            "Gift": "gift",
            "Gloves": "gloves",
        }

        # 加载所有Schema数据
        self.definitions = self._load_json("definitions.json")
        self.paints = self._load_json("paints.json")
        self.sticker_kits = self._load_json("sticker_kits.json")
        self.music_kits = self._load_json("music_kits.json")
        self.musics = self._load_json("musics.json")
        self.containers = self._load_json("containers.json")
        self.items = self._load_json("items.json")
        self.types = self._load_json("types.json")

    def _load_json(self, filename: str) -> dict:
        """加载JSON文件"""
        filepath = self.schemas_dir / filename
        try:
            with open(filepath, encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Warning: {filename} not found in {self.schemas_dir}")
            return {}

    def _get_default_description(self) -> dict[str, str]:
        """获取默认描述"""
        return {"zh-CN": "", "en-US": ""}

    def _get_item_type(self, type_id: str) -> str:
        """根据type_id获取物品类型"""
        type_name = self.types.get(type_id, "weapon")
        return self.type_mapping.get(type_name, "weapon")

    def _get_item_name(self, paint_id: str, def_id: str) -> str:
        item_key = f"[{paint_id}]{def_id}"
        item_data = self.items.get(item_key, {})
        return item_data.get("name", "")

    def _get_item_image(self, paint_id: str, def_id: str) -> str | None:
        """从items.json获取物品图片"""
        item_key = f"[{paint_id}]{def_id}"
        item_data = self.items.get(item_key, {})
        return item_data.get("image")

    def _format_paint_item(self, paint_id: str, paint_data: dict) -> list[CS2Item]:
        """格式化涂装物品"""
        items = []
        paint_name = paint_data.get("name", f"Paint_{paint_id}")
        paint_name_zh = paint_data.get("name_zh", paint_name)

        # 查找使用此涂装的武器
        for def_id, def_data in self.definitions.items():
            if f"[{paint_id}]{def_id}" not in self.items:
                continue
            item_type = self._get_item_type(def_data.get("type", "0"))
            item_name = self._get_item_name(paint_id, def_id)
            if item_type == "weapon":
                slug_name = f"{item_name.lower().replace(' ', '_')}_{paint_name.lower().replace(' ', '_')}"

                name = {
                    "zh-CN": f"{def_data.get('name_zh', f'Weapon_{def_id}')} | {paint_name_zh}",
                    "en-US": f"{def_data.get('name', f'Weapon_{def_id}')} | {paint_name}",
                }

                # 获取图片链接
                cover_image = self._get_item_image(paint_id, def_id)

                item = CS2Item(
                    slug_name=slug_name,
                    name=name,
                    description=self._get_default_description(),
                    cover_image=cover_image,
                    item_type=item_type,
                    weapon_defindex=int(def_id),
                    weapon_name=item_name,
                    paint_id=int(paint_id),
                    item_id=None,
                    team=None,
                    model=None,
                    agent_name=self._get_default_description(),
                )
                items.append(item)

        return items

    def _format_sticker_item(self, sticker_id: str, sticker_data: dict) -> CS2Item:
        """格式化印花物品"""
        name = {
            "zh-CN": sticker_data.get("name_chinese", sticker_data.get("name", f"Sticker_{sticker_id}")),
            "en-US": sticker_data.get("name_english", sticker_data.get("name", f"Sticker_{sticker_id}")),
        }

        description = {
            "zh-CN": sticker_data.get("description_chinese", ""),
            "en-US": sticker_data.get("description_english", ""),
        }

        slug_name = name["en-US"].lower().replace(" ", "_").replace("|", "").replace("(", "").replace(")", "")

        return CS2Item(
            slug_name=slug_name,
            name=name,
            description=description,
            cover_image=sticker_data.get("image"),
            item_type="sticker",
            weapon_defindex=None,
            weapon_name=None,
            paint_id=None,
            item_id=int(sticker_id),
            team=None,
            model=None,
            agent_name=self._get_default_description(),
        )

    def _format_music_kit_item(self, kit_id: str, kit_data: dict) -> CS2Item:
        """格式化音乐盒物品"""
        # 获取音乐信息
        music_ids = kit_data.get("musics", [])
        music_name = ""
        music_name_zh = ""

        if music_ids:
            music_id = music_ids[0]
            music_info = self.musics.get(music_id, {})
            music_name = music_info.get("name", f"Music_{music_id}")
            music_name_zh = music_info.get("name_zh", music_name)

        name = {"zh-CN": music_name_zh, "en-US": music_name}

        slug_name = f"music_kit_{music_name.lower().replace(' ', '_').replace(',', '').replace('-', '_')}"

        return CS2Item(
            slug_name=slug_name,
            name=name,
            description=self._get_default_description(),
            cover_image=None,
            item_type="music_kit",
            weapon_defindex=None,
            weapon_name=None,
            paint_id=None,
            item_id=int(kit_id),
            team=None,
            model=None,
            agent_name=self._get_default_description(),
        )

    def _format_definition_item(self, def_id: str, def_data: dict) -> CS2Item:
        """格式化定义物品"""
        item_type = self._get_item_type(def_data.get("type", "0"))
        item_name = def_data.get("name", f"Item_{def_id}")

        name = {
            "zh-CN": item_name,  # 这里可以添加中文翻译逻辑
            "en-US": item_name,
        }

        slug_name = item_name.lower().replace(" ", "_").replace("-", "_")

        # 如果是Agent类型，设置agent_name
        agent_name = self._get_default_description()
        if item_type == "agent":
            agent_name = name.copy()

        # 尝试从items.json获取图片 (通常只有def_id的物品)
        cover_image = None
        direct_item = self.items.get(def_id, {})
        if direct_item.get("image"):
            cover_image = direct_item["image"]

        return CS2Item(
            slug_name=slug_name,
            name=name,
            description=self._get_default_description(),
            cover_image=cover_image,
            item_type=item_type,
            weapon_defindex=int(def_id) if item_type == "weapon" else None,
            weapon_name=item_name if item_type == "weapon" else None,
            paint_id=None,
            item_id=int(def_id),
            team=None,
            model=None,
            agent_name=agent_name,
        )

    def _format_container_item(self, container_id: str, container_data: dict) -> CS2Item:
        """格式化容器物品"""
        # 查找关联的定义项
        associated_id = container_data.get("associated")
        container_name = f"Container_{container_id}"

        if associated_id and associated_id in self.definitions:
            def_data = self.definitions[associated_id]
            container_name = def_data.get("name", container_name)

        name = {
            "zh-CN": container_name,  # 这里可以添加中文翻译逻辑
            "en-US": container_name,
        }

        slug_name = container_name.lower().replace(" ", "_").replace("-", "_")

        return CS2Item(
            slug_name=slug_name,
            name=name,
            description=self._get_default_description(),
            cover_image=None,
            item_type="case",
            weapon_defindex=None,
            weapon_name=None,
            paint_id=None,
            item_id=int(container_id),
            team=None,
            model=None,
            agent_name=self._get_default_description(),
        )

    def format_all_items(self) -> list[dict]:
        """格式化所有物品"""
        all_items = []

        # 格式化涂装物品
        print("Processing paint items...")
        for paint_id, paint_data in self.paints.items():
            paint_items = self._format_paint_item(paint_id, paint_data)
            all_items.extend([asdict(item) for item in paint_items])

        # 格式化印花物品
        print("Processing sticker items...")
        for sticker_id, sticker_data in self.sticker_kits.items():
            if sticker_id != "0":  # 跳过模板项
                sticker_item = self._format_sticker_item(sticker_id, sticker_data)
                all_items.append(asdict(sticker_item))

        # 格式化音乐盒物品
        print("Processing music kit items...")
        for kit_id, kit_data in self.music_kits.items():
            music_kit_item = self._format_music_kit_item(kit_id, kit_data)
            all_items.append(asdict(music_kit_item))

        # 格式化定义物品（非武器的其他物品）
        print("Processing definition items...")
        for def_id, def_data in self.definitions.items():
            item_type = self._get_item_type(def_data.get("type", "0"))
            # 跳过武器类型，因为已经在涂装中处理了
            if item_type != "weapon":
                def_item = self._format_definition_item(def_id, def_data)
                all_items.append(asdict(def_item))

        # 格式化容器物品
        print("Processing container items...")
        for container_id, container_data in self.containers.items():
            container_item = self._format_container_item(container_id, container_data)
            all_items.append(asdict(container_item))

        print(f"Total items processed: {len(all_items)}")
        return all_items

    def save_formatted_items(self, output_file: str | Path | None = None) -> list[dict]:
        """保存格式化后的物品数据"""
        if output_file is None:
            output_file = self.schemas_dir / "formatted_items.json"
        else:
            output_file = Path(output_file)

        items = self.format_all_items()

        # 确保输出目录存在
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(items, f, ensure_ascii=False, indent=2)

        print(f"Formatted items saved to {output_file}")
        return items
