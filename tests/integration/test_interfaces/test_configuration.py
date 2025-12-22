# class TestConfigIntegration:
#     """Tests d'intégration configuration"""
    
#     def test_load_validate_save_cycle(self, minimal_config, tmp_path):
#         """Test : cycle complet load -> validate -> save"""
#         # 1. Sauvegarder
#         config_path = tmp_path / "config.json"
#         ConfigLoader.save(minimal_config, config_path)
        
#         # 2. Charger
#         loaded = ConfigLoader.load(config_path)
        
#         # 3. Valider
#         ConfigValidator.validate(loaded)  # Ne doit pas planter
        
#         # 4. Re-sauvegarder
#         config_path2 = tmp_path / "config2.json"
#         ConfigLoader.save(loaded, config_path2)
        
#         # 5. Vérifier identité
#         loaded2 = ConfigLoader.load(config_path2)
#         assert loaded['name'] == loaded2['name']
    
#     def test_invalid_config_caught(self, invalid_config, tmp_path):
#         """Test : config invalide détectée"""
#         # Sauvegarder la config invalide
#         config_path = tmp_path / "invalid.json"
#         with open(config_path, 'w') as f:
#             json.dump(invalid_config, f)
        
#         # Charger (devrait réussir)
#         loaded = ConfigLoader.load(config_path)
        
#         # Valider (devrait échouer)
#         with pytest.raises(ValueError):
#             ConfigValidator.validate(loaded)