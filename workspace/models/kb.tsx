import React, { useState, useEffect } from 'react';
import { MoreVertical, Trash2, Edit2, ChevronLeft, ChevronRight } from 'lucide-react';
import { Category, Habit, HabitCompletion } from '../types';
import HabitCard from './HabitCard';
import { getToday } from '../utils/dateUtils';
import { getCategoryColor } from '../utils/categoryColors';

interface KanbanBoardProps {
  categories: Category[];
  habits: Habit[];
  completions: HabitCompletion[];
  onCompleteHabit: (habit: Habit) => void;
  onHabitClick: (habit: Habit) => void;
  onEditHabit: (habit: Habit) => void;
  onEditCompletion?: (habit: Habit) => void;
  onShareHabit?: (habit: Habit) => void;
  onDeleteCategory: (categoryId: string) => void;
  onUpdateCategoryName: (categoryId: string, newName: string) => void;
  currentCategoryIndex: number;
  onCategoryIndexChange: (index: number) => void;
}

const KanbanBoard: React.FC<KanbanBoardProps> = ({
  categories,
  habits,
  completions,
  onCompleteHabit,
  onHabitClick,
  onEditHabit,
  onEditCompletion,
  onShareHabit,
  onDeleteCategory,
  onUpdateCategoryName,
  currentCategoryIndex,
  onCategoryIndexChange
}) => {
  const [openDropdown, setOpenDropdown] = useState<string | null>(null);
  const kanbanContainerRef = React.useRef<HTMLDivElement>(null);
  const [editingCategory, setEditingCategory] = useState<string | null>(null);
  const [editingName, setEditingName] = useState('');

  // Assign consistent colors to categories
  const categoriesWithColors = categories.map((category, index) => ({
    ...category,
    color: getCategoryColor(index)
  }));

  // Reset category index if it's out of bounds
  useEffect(() => {
       if (kanbanContainerRef.current && categoriesWithColors.length > 0) {
       const validIndex = currentCategoryIndex % categoriesWithColors.length;
       if (validIndex !== currentCategoryIndex) {
         onCategoryIndexChange(validIndex);
      }

      const categoryElement = kanbanContainerRef.current.children[validIndex] as HTMLElement;
      if (categoryElement) {
        kanbanContainerRef.current.scrollTo({
          left: categoryElement.offsetLeft,
          behavior: 'smooth',
+        });
+      }
    }
  }, [categoriesWithColors.length, currentCategoryIndex, onCategoryIndexChange]);

  const handleDeleteCategory = (categoryId: string) => {
    if (window.confirm('Are you sure you want to delete this category? All habits will be moved to the first available category.')) {
      onDeleteCategory(categoryId);
    }
    setOpenDropdown(null);
  };

  const handleEditCategory = (category: Category) => {
    setEditingCategory(category.id);
    setEditingName(category.name);
    setOpenDropdown(null);
  };

  const handleSaveCategoryName = (categoryId: string) => {
    if (editingName.trim()) {
      onUpdateCategoryName(categoryId, editingName.trim());
    }
    setEditingCategory(null);
    setEditingName('');
  };

  const handleCancelEdit = () => {
    setEditingCategory(null);
    setEditingName('');
  };

  const sortHabits = (categoryHabits: Habit[]) => {
    const today = getToday();
    
    return categoryHabits.sort((a, b) => {
      const aCompleted = completions.some(c => c.habitId === a.id && c.date === today);
      const bCompleted = completions.some(c => c.habitId === b.id && c.date === today);
      
      // Push completed habits to bottom
      if (aCompleted && !bCompleted) return 1;
      if (!aCompleted && bCompleted) return -1;
      
      // If both have same completion status, maintain original order
      return 0;
    });
  };

  // Mobile navigation
  const nextCategory = () => {
    onCategoryIndexChange((currentCategoryIndex + 1) % categoriesWithColors.length);
  };

  const prevCategory = () => {
    onCategoryIndexChange((currentCategoryIndex - 1 + categoriesWithColors.length) % categoriesWithColors.length);
  };

  // Calculate visible categories for desktop (show current + next 2)
  const getVisibleCategories = () => {
    if (categoriesWithColors.length <= 3) {
      return categoriesWithColors;
    }
    
    const visible = [];
    for (let i = 0; i < 3; i++) {
      const index = (currentCategoryIndex + i) % categoriesWithColors.length;
      visible.push(categoriesWithColors[index]);
    }
    return visible;
  };

  const visibleCategories = getVisibleCategories();

  return (
    <>
      {/* Desktop View - Show 3 categories at a time */}
      <div className="hidden md:block">
        <div className="flex gap-8 pb-4">
          {visibleCategories.map((category, displayIndex) => {
            const categoryHabits = habits.filter(habit => habit.category === category.id);
            const sortedHabits = sortHabits(categoryHabits);
            const isCurrentCategory = displayIndex === 0; // First visible category is the "current" one
            
            return (
              <div 
                key={category.id} 
                className={`flex-shrink-0 animate-scale-in transition-all duration-300 ${
                  isCurrentCategory ? 'opacity-100' : 'opacity-75'
                }`} 
                style={{ width: '320px' }}
              >
                {/* Category Header */}
                <div className="mb-6">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center flex-1">
                      {editingCategory === category.id ? (
                        <div className="flex items-center space-x-2 flex-1">
                          <input
                            type="text"
                            value={editingName}
                            onChange={(e) => setEditingName(e.target.value)}
                            onKeyDown={(e) => {
                              if (e.key === 'Enter') {
                                handleSaveCategoryName(category.id);
                              } else if (e.key === 'Escape') {
                                handleCancelEdit();
                              }
                            }}
                            className="flex-1 px-3 py-1 text-lg font-medium text-gray-900 dark:text-white bg-transparent focus:outline-none focus:ring-2 focus:ring-primary-400 rounded-lg"
                            autoFocus
                          />
                          <button
                            onClick={() => handleSaveCategoryName(category.id)}
                            className="p-1 text-primary-500 hover:text-primary-600 transition-colors"
                          >
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                            </svg>
                          </button>
                          <button
                            onClick={handleCancelEdit}
                            className="p-1 text-gray-400 hover:text-gray-600 transition-colors"
                          >
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                            </svg>
                          </button>
                        </div>
                      ) : (
                        <h3 className="text-lg font-medium text-gray-900 dark:text-white">
                          {category.name}
                        </h3>
                      )}
                      <span className="ml-3 px-2 py-1 text-xs font-medium text-gray-500 dark:text-gray-400 bg-gray-100 dark:bg-gray-700 rounded-full">
                        {categoryHabits.length}
                      </span>
                    </div>
                    
                    {categoriesWithColors.length > 1 && (
                      <div className="relative ml-2">
                        <button
                          onClick={() => setOpenDropdown(openDropdown === category.id ? null : category.id)}
                          className="p-1 rounded-lg text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
                        >
                          <MoreVertical className="w-4 h-4" />
                        </button>
                        
                        {openDropdown === category.id && (
                          <div className="absolute right-0 top-8 w-48 bg-white dark:bg-gray-800 rounded-lg shadow-lg py-1 z-10">
                            <button
                              onClick={() => handleEditCategory(category)}
                              className="w-full px-4 py-2 text-left text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 flex items-center"
                            >
                              <Edit2 className="w-4 h-4 mr-2" />
                              Edit Name
                            </button>
                            <button
                              onClick={() => handleDeleteCategory(category.id)}
                              className="w-full px-4 py-2 text-left text-sm text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 flex items-center"
                            >
                              <Trash2 className="w-4 h-4 mr-2" />
                              Delete Category
                            </button>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                </div>
                
                {/* Habits Column */}
                <div className="space-y-4">
                  {sortedHabits.length === 0 ? (
                    <div className="text-center py-12">
                      <div className="w-12 h-12 bg-gray-100 dark:bg-gray-700 rounded-xl mx-auto mb-3 flex items-center justify-center">
                        <svg className="w-6 h-6 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                        </svg>
                      </div>
                      <p className="text-sm text-gray-500 dark:text-gray-400">
                        No habits yet
                      </p>
                    </div>
                  ) : (
                    sortedHabits.map(habit => (
                      <HabitCard
                        key={habit.id}
                        habit={habit}
                        category={category}
                        completions={completions}
                        onComplete={onCompleteHabit}
                        onClick={onHabitClick}
                        onEdit={onEditHabit}
                        onEditCompletion={onEditCompletion}
                        onShareHabit={onShareHabit}
                      />
                    ))
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Mobile View - Single Category with Navigation */}
      <div className="md:hidden">
        {categoriesWithColors.length > 0 && (
          <div className="animate-scale-in">
            {/* Mobile Category Header with Navigation */}
            <div className="mb-6">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-4">
                  {categoriesWithColors.length > 1 && (
                    <button
                      onClick={prevCategory}
                      className="p-2 rounded-lg text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
                    >
                      <ChevronLeft className="w-5 h-5" />
                    </button>
                  )}
                  
                  <div className="flex items-center">
                    {editingCategory === categoriesWithColors[currentCategoryIndex]?.id ? (
                      <div className="flex items-center space-x-2">
                        <input
                          type="text"
                          value={editingName}
                          onChange={(e) => setEditingName(e.target.value)}
                          onKeyDown={(e) => {
                            if (e.key === 'Enter') {
                              handleSaveCategoryName(categoriesWithColors[currentCategoryIndex].id);
                            } else if (e.key === 'Escape') {
                              handleCancelEdit();
                            }
                          }}
                          className="px-3 py-1 text-lg font-medium text-gray-900 dark:text-white bg-transparent focus:outline-none focus:ring-2 focus:ring-primary-400 rounded-lg"
                          autoFocus
                        />
                        <button
                          onClick={() => handleSaveCategoryName(categoriesWithColors[currentCategoryIndex].id)}
                          className="p-1 text-primary-500 hover:text-primary-600 transition-colors"
                        >
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                          </svg>
                        </button>
                        <button
                          onClick={handleCancelEdit}
                          className="p-1 text-gray-400 hover:text-gray-600 transition-colors"
                        >
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                          </svg>
                        </button>
                      </div>
                    ) : (
                      <h3 className="text-lg font-medium text-gray-900 dark:text-white">
                        {categoriesWithColors[currentCategoryIndex]?.name}
                      </h3>
                    )}
                    <span className="ml-3 px-2 py-1 text-xs font-medium text-gray-500 dark:text-gray-400 bg-gray-100 dark:bg-gray-700 rounded-full">
                      {habits.filter(h => h.category === categoriesWithColors[currentCategoryIndex]?.id).length}
                    </span>
                  </div>

                  {categoriesWithColors.length > 1 && (
                    <button
                      onClick={nextCategory}
                      className="p-2 rounded-lg text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
                    >
                      <ChevronRight className="w-5 h-5" />
                    </button>
                  )}
                </div>
                
                {categoriesWithColors.length > 1 && (
                  <div className="relative">
                    <button
                      onClick={() => setOpenDropdown(openDropdown === categoriesWithColors[currentCategoryIndex]?.id ? null : categoriesWithColors[currentCategoryIndex]?.id)}
                      className="p-1 rounded-lg text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
                    >
                      <MoreVertical className="w-4 h-4" />
                    </button>
                    
                    {openDropdown === categoriesWithColors[currentCategoryIndex]?.id && (
                      <div className="absolute right-0 top-8 w-48 bg-white dark:bg-gray-800 rounded-lg shadow-lg py-1 z-10">
                        <button
                          onClick={() => handleEditCategory(categoriesWithColors[currentCategoryIndex])}
                          className="w-full px-4 py-2 text-left text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 flex items-center"
                        >
                          <Edit2 className="w-4 h-4 mr-2" />
                          Edit Name
                        </button>
                        <button
                          onClick={() => handleDeleteCategory(categoriesWithColors[currentCategoryIndex].id)}
                          className="w-full px-4 py-2 text-left text-sm text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 flex items-center"
                        >
                          <Trash2 className="w-4 h-4 mr-2" />
                          Delete Category
                        </button>
                      </div>
                    )}
                  </div>
                )}
              </div>

              {/* Category indicator dots */}
              {categoriesWithColors.length > 1 && (
                <div className="flex justify-center mt-4 space-x-2">
                  {categoriesWithColors.map((_, index) => (
                    <button
                      key={index}
                      onClick={() => onCategoryIndexChange(index)}
                      className={`w-2 h-2 rounded-full transition-colors ${
                        index === currentCategoryIndex
                          ? 'bg-primary-500'
                          : 'bg-gray-300 dark:bg-gray-600'
                      }`}
                    />
                  ))}
                </div>
              )}
            </div>
            
            {/* Mobile Habits List */}
            <div className="space-y-4">
              {(() => {
                const currentCategory = categoriesWithColors[currentCategoryIndex];
                if (!currentCategory) return null;
                
                const categoryHabits = habits.filter(habit => habit.category === currentCategory.id);
                const sortedHabits = sortHabits(categoryHabits);
                
                if (sortedHabits.length === 0) {
                  return (
                    <div className="text-center py-12">
                      <div className="w-12 h-12 bg-gray-100 dark:bg-gray-700 rounded-xl mx-auto mb-3 flex items-center justify-center">
                        <svg className="w-6 h-6 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                        </svg>
                      </div>
                      <p className="text-sm text-gray-500 dark:text-gray-400">
                        No habits yet
                      </p>
                    </div>
                  );
                }
                
                return sortedHabits.map(habit => (
                  <div key={habit.id} className="w-full">
                    <HabitCard
                      habit={habit}
                      category={currentCategory}
                      completions={completions}
                      onComplete={onCompleteHabit}
                      onClick={onHabitClick}
                      onEdit={onEditHabit}
                      onEditCompletion={onEditCompletion}
                      onShareHabit={onShareHabit}
                    />
                  </div>
                ));
              })()}
            </div>
          </div>
        )}
      </div>
    </>
  );
};

export default KanbanBoard;