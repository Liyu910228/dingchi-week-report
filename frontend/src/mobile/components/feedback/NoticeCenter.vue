<script setup lang="ts">
import { useNoticeStore } from "@/app/stores/notice"

const noticeStore = useNoticeStore()
</script>

<template>
  <Teleport to="body">
    <div class="notice-center" aria-live="polite" aria-label="系统通知">
      <TransitionGroup name="notice" tag="div" class="notice-center__list">
        <div
          v-for="notice in noticeStore.notices"
          :key="notice.id"
          class="notice-card"
          :class="`notice-card--${notice.type}`"
          role="alert"
        >
          <span class="notice-card__message">{{ notice.message }}</span>
          <button
            v-if="notice.type === 'warning'"
            class="notice-card__close"
            type="button"
            aria-label="关闭通知"
            @click="noticeStore.remove(notice.id)"
          >
            ×
          </button>
        </div>
      </TransitionGroup>
    </div>
  </Teleport>
</template>

<style scoped src="./NoticeCenter.css"></style>
