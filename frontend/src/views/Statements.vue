<script setup>
import { onMounted } from 'vue'
import { useStatementsStore } from '@/stores/statements.js'
import { useSettingsStore } from '@/stores/settings.js'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Label } from '@/components/ui/label'
import { FileText, Upload, Play, Trash2, Download } from 'lucide-vue-next'

const statementsStore = useStatementsStore()
const settingsStore = useSettingsStore()

onMounted(() => {
  statementsStore.fetchStatements()
})

const handleFileUpload = (event) => {
  const files = Array.from(event.target.files)
  if (files.length === 1) {
    statementsStore.uploadStatement(files[0])
  } else if (files.length > 1) {
    statementsStore.uploadMultipleStatements(files)
  }
  // Clear input
  event.target.value = ''
}

const formatDate = (dateString) => {
  return new Date(dateString).toLocaleDateString()
}

const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

const triggerFileUpload = () => {
  const fileInput = document.getElementById('file-upload')
  if (fileInput) {
    fileInput.click()
  }
}
</script>

<template>
  <div class="p-6">
    <div class="mb-6">
      <h1 class="text-2xl font-bold mb-2">Statements</h1>
      <p class="text-sm text-muted-foreground">Manage your financial statement files</p>
    </div>

    <!-- Upload Section -->
    <Card class="mb-6">
      <CardHeader class="pb-4">
        <CardTitle class="text-lg flex items-center gap-2">
          <Upload class="h-5 w-5" />
          Upload Statements
        </CardTitle>
        <CardDescription>Upload CSV, XLSX, or XLS files</CardDescription>
      </CardHeader>
      <CardContent>
        <div class="space-y-4">
          <div class="flex items-center gap-4">
            <input
              type="file"
              id="file-upload"
              multiple
              accept=".csv,.xlsx,.xls"
              @change="handleFileUpload"
              class="hidden"
            />
            <Button
              @click="triggerFileUpload"
              :disabled="statementsStore.loading"
            >
              <Upload class="h-4 w-4 mr-2" />
              Choose Files
            </Button>
            <span class="text-sm text-muted-foreground">
              Supported formats: CSV, XLSX, XLS
            </span>
          </div>
          
          <div class="flex items-center space-x-2">
            <input
              id="auto-process-toggle"
              v-model="settingsStore.autoProcess"
              @change="settingsStore.setAutoProcess(settingsStore.autoProcess)"
              type="checkbox"
              class="h-4 w-4 text-primary focus:ring-primary border-gray-300 rounded"
            />
            <Label for="auto-process-toggle" class="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70">
              Auto-process after upload
            </Label>
          </div>
        </div>
        
        <!-- Upload Progress -->
        <div v-if="statementsStore.uploadProgress > 0" class="mt-4">
          <div class="w-full bg-muted rounded-full h-2">
            <div
              class="bg-primary h-2 rounded-full transition-all duration-300"
              :style="{ width: `${statementsStore.uploadProgress}%` }"
            ></div>
          </div>
          <p class="text-sm text-muted-foreground mt-1">
            Upload progress: {{ statementsStore.uploadProgress }}%
          </p>
        </div>
      </CardContent>
    </Card>

    <!-- Statements List -->
    <Card>
      <CardHeader class="pb-4">
        <div class="flex items-center justify-between">
          <div>
            <CardTitle class="text-lg flex items-center gap-2">
              <FileText class="h-5 w-5" />
              Statements ({{ statementsStore.totalCount }})
            </CardTitle>
            <CardDescription>
              {{ statementsStore.processedStatements.length }} processed, 
              {{ statementsStore.unprocessedStatements.length }} pending
            </CardDescription>
          </div>
          <Button
            @click="statementsStore.fetchStatements()"
            variant="outline"
            size="sm"
            :disabled="statementsStore.loading"
          >
            Refresh
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        <div v-if="statementsStore.loading && !statementsStore.hasStatements" class="text-center py-8">
          <p class="text-muted-foreground">Loading statements...</p>
        </div>
        
        <div v-else-if="!statementsStore.hasStatements" class="text-center py-8">
          <FileText class="h-12 w-12 mx-auto text-muted-foreground mb-4" />
          <p class="text-muted-foreground mb-2">No statements uploaded yet</p>
          <p class="text-sm text-muted-foreground">Upload your first statement file to get started</p>
        </div>
        
        <div v-else class="space-y-3">
          <div
            v-for="statement in statementsStore.statements"
            :key="statement.id"
            class="flex items-center justify-between p-4 border rounded-lg hover:bg-muted/50 transition-colors"
          >
            <div class="flex items-center gap-3">
              <FileText class="h-8 w-8 text-muted-foreground" />
              <div>
                <div class="font-medium">{{ statement.filename }}</div>
                <div class="text-sm text-muted-foreground">
                  Uploaded {{ formatDate(statement.created_at) }}
                  <span v-if="statement.mime_type" class="ml-2">
                    • {{ statement.mime_type }}
                  </span>
                </div>
              </div>
            </div>
            
            <div class="flex items-center gap-2">
              <Badge :variant="statement.processed ? 'default' : 'secondary'">
                {{ statement.processed ? 'Processed' : 'Pending' }}
              </Badge>
              
              <Button
                v-if="!statement.processed"
                @click="statementsStore.processStatement(statement.id)"
                size="sm"
                variant="outline"
              >
                <Play class="h-3 w-3 mr-1" />
                Process
              </Button>
              
              <Button
                @click="statementsStore.deleteStatement(statement.id)"
                size="sm"
                variant="outline"
                class="text-destructive hover:text-destructive"
              >
                <Trash2 class="h-3 w-3" />
              </Button>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  </div>
</template>
