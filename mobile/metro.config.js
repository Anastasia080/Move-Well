const { getDefaultConfig, mergeConfig } = require('@react-native/metro-config');

const defaultConfig = getDefaultConfig(__dirname);

const config = {
  watchman: false,
  resolver: {
    assetExts: [
      ...defaultConfig.resolver.assetExts,
      'mp4', 'mov', 'avi', 'wmv', 'm4v',
    ],
  },
};

module.exports = mergeConfig(defaultConfig, config);
