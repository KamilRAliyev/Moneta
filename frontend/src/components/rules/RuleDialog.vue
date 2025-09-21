<template>
  <div class="fixed inset-0 bg-background/80 backdrop-blur-sm flex items-center justify-center p-4 z-50">
    <Card class="max-w-4xl w-full max-h-[90vh] overflow-hidden">
      <!-- Header -->
      <CardHeader class="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle class="text-xl">
          {{ isEdit ? 'Edit Rule' : 'Create New Rule' }}
        </CardTitle>
        <Button 
          @click="$emit('close')"
          variant="ghost"
          size="icon"
        >
          <X class="w-4 h-4" />
        </Button>
      </CardHeader>

      <!-- Content -->
      <CardContent class="overflow-y-auto max-h-[calc(90vh-140px)]">
        <RuleEditor 
          :rule="localRule"
          :transaction-fields="transactionFields"
          :formula-commands="formulaCommands"
          @update:rule="updateRule"
          @test="handleTest"
        />
      </CardContent>

      <!-- Footer -->
      <div class="flex items-center justify-between p-6 border-t bg-muted/50">
        <div class="flex items-center space-x-3">
          <Button 
            @click="handleTest"
            variant="outline"
          >
            <TestTube class="w-4 h-4 mr-2" />
            Test Rule
          </Button>
        </div>
        
        <div class="flex items-center space-x-3">
          <Button 
            @click="$emit('close')"
            variant="outline"
          >
            Cancel
          </Button>
          <Button 
            @click="handleSave"
            :disabled="!isValid"
          >
            {{ isEdit ? 'Update Rule' : 'Create Rule' }}
          </Button>
        </div>
      </div>
    </Card>

    <!-- Test Dialog -->
    <RuleTestDialog
      v-if="showTestDialog"
      :rule="localRule"
      :transaction-fields="transactionFields"
      @close="closeTestDialog"
    />
  </div>
</template>

<script>
import { ref, computed, toRefs } from 'vue'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import RuleEditor from './RuleEditor.vue'
import RuleTestDialog from './RuleTestDialog.vue'
import { X, TestTube } from 'lucide-vue-next'

export default {
  name: 'RuleDialog',
  components: {
    Button,
    Card,
    CardContent,
    CardHeader,
    CardTitle,
    RuleEditor,
    RuleTestDialog,
    X,
    TestTube
  },
  props: {
    rule: {
      type: Object,
      required: true
    },
    transactionFields: {
      type: Array,
      default: () => []
    },
    formulaCommands: {
      type: Array,
      default: () => []
    }
  },
  emits: ['save', 'close'],
  setup(props, { emit }) {
    const { rule } = toRefs(props)
    
    // State
    const localRule = ref({ ...rule.value })
    const showTestDialog = ref(false)

    // Computed
    const isEdit = computed(() => !!localRule.value.id)
    
    const isValid = computed(() => {
      return localRule.value.name?.trim() && 
             localRule.value.target_field?.trim() && 
             localRule.value.action?.trim()
    })

    // Methods
    const updateRule = (updatedRule) => {
      localRule.value = { ...updatedRule }
    }

    const handleSave = () => {
      if (!isValid.value) return
      
      const ruleData = { ...localRule.value }
      
      // Clean up empty fields
      if (!ruleData.condition?.trim()) {
        ruleData.condition = null
      }
      if (!ruleData.description?.trim()) {
        ruleData.description = null
      }
      
      emit('save', ruleData)
    }

    const handleTest = () => {
      showTestDialog.value = true
    }

    const closeTestDialog = () => {
      showTestDialog.value = false
    }

    return {
      localRule,
      showTestDialog,
      isEdit,
      isValid,
      updateRule,
      handleSave,
      handleTest,
      closeTestDialog
    }
  }
}
</script>
