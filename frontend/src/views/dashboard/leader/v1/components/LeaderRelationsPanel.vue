<script setup lang="ts">
import { Link2, UsersRound } from "lucide-vue-next"

import type { LeaderRelation } from "../types"

const props = defineProps<{ relations: LeaderRelation[] }>()
</script>

<template>
  <article class="leader-relations-panel">
    <div class="leader-bottom-heading"><div class="leader-bottom-title"><span class="leader-bottom-icon leader-bottom-icon--green"><UsersRound :size="17" /></span><h2>协同关系</h2></div><Link2 :size="18" class="leader-relations-link" /></div>
    <div v-if="!props.relations.length" class="leader-bottom-empty">暂无协同记录</div>
    <div v-else class="leader-relation-map">
      <div class="leader-relation-side leader-relation-side--left">
        <div v-for="relation in props.relations.slice(0, 3)" :key="relation.id" class="leader-relation-node"><span>{{ relation.name.slice(0, 1) }}</span><strong :title="relation.name">{{ relation.name }}</strong><small>{{ relation.count }}</small></div>
      </div>
      <div class="leader-relation-center"><UsersRound :size="25" /><strong>协同中心</strong></div>
      <div class="leader-relation-side leader-relation-side--right">
        <div v-for="relation in props.relations.slice(3, 6)" :key="relation.id" class="leader-relation-node"><span>{{ relation.name.slice(0, 1) }}</span><strong :title="relation.name">{{ relation.name }}</strong><small>{{ relation.count }}</small></div>
      </div>
    </div>
  </article>
</template>

<style scoped src="./LeaderRelationsPanel.css"></style>
