import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
} from 'react-native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { useNavigation } from '@react-navigation/native';
import { useTheme } from '../ThemeContext';

type RootStackParamList = {
  Legs: { category: string } | undefined;
  Hands: { category: string } | undefined;
  Body: { category: string } | undefined;
  All: { category: string } | undefined;
};
type CategoryScreenNavigationProp = NativeStackNavigationProp<RootStackParamList>;

const Category = () => {
    const { colors } = useTheme();
    const navigation = useNavigation<CategoryScreenNavigationProp>();

    const categories = [
    { id: 1, title: 'Ноги', screen: 'Legs', category: 'legs' },
    { id: 2, title: 'Руки', screen: 'Hands', category: 'hands' },
    { id: 3, title: 'Корпус', screen: 'Body', category: 'body' },
    { id: 4, title: 'Все', screen: 'All', category: '' },
  ];

  const handleCategoryPress = (screenName: keyof RootStackParamList, category: string) => {
    navigation.navigate(screenName as any, { category });
  };


  return (
    <View style={styles.categorySection}>
          <Text style={[styles.categoryTitle, { color: colors.text }]}>Категории</Text>
          <View style={styles.categoriesGrid}>
            {categories.map((category) => (
              <TouchableOpacity 
                key={category.id}
                style={[styles.categoryItem, { backgroundColor: colors.primary }]}
                onPress={() => handleCategoryPress(category.screen as keyof RootStackParamList, category.category)}
              >
                <Text style={styles.categoryText}>{category.title}</Text>
              </TouchableOpacity>
            ))}
          </View>
    </View>

  );
};

const styles = StyleSheet.create({
  categorySection: {
    display: 'flex',
    flexDirection: 'column',
    marginBottom: 10,
  },
  categoryTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    marginBottom: 15,
  },
  categoriesGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
  },
  categoryItem: {
    width: '48%',
    height: 100,
    borderRadius: 12,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 15,
  },
  categoryText: {
    color: '#fff',
    fontSize: 18,
    fontWeight: 'bold',
  },
});

export default Category;