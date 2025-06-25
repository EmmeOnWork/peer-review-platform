<template>
  <div class="submission-details-page">
    <h1>Dettagli Submission</h1>
    <SubmissionDetails />
  </div>
</template>

<script>
import SubmissionDetails from '@/components/submission/SubmissionDetails.vue';

export default {
  name: 'SubmissionDetailsPage',
  components: {
    SubmissionDetails
  }
};
</script>

<style scoped>
.submission-details-page {
  max-width: 900px;
  margin: 20px auto;
  padding: 20px;
}

h1 {
  text-align: center;
  margin-bottom: 20px;
}
</style>