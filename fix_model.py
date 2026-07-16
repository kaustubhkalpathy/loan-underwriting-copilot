import lightgbm as lgb
booster = lgb.Booster(model_file='Datasets/lgbm_booster.txt')
booster.save_model('Datasets/lgbm_booster_compat.txt')
print('Done')