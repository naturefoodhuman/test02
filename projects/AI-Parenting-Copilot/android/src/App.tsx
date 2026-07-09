// 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
// 创建时间（北京时间）：2026-07-09 11:10:00


import React from 'react';
import { SafeAreaView, Text, View } from 'react-native';

import { routes } from './navigation/routes';
import { colors } from './theme/colors';

export function App(): React.JSX.Element {
  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: colors.light.background }}>
      <View style={{ padding: 24 }}>
        <Text style={{ color: colors.light.foreground, fontSize: 24, fontWeight: '700' }}>
          AI Parenting Copilot
        </Text>
        <Text>Android-only shell ready: {routes.Today}</Text>
      </View>
    </SafeAreaView>
  );
}

export default App;
