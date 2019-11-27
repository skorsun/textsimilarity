<template>
  <div class="container">
    <div class="row">
      <div class="col-sm-10">
        <h1>Texts</h1>
        <hr><br><br>
        <alert :message=message v-if="showMessage" ></alert>
        <button type="button" class="btn btn-success btn-sm" v-b-modal.text-modal>Add Text</button>
        <br><br>
        <table class="table table-hover">
          <thead>
            <tr>
              <th scope="col">Id</th>
              <th scope="col">Content</th>
               <th></th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="currentPage"><td></td>
              <td><button type="button" class="btn btn-sm" @click="onPreviousPage()">
             Previous</button></td></tr>
            <tr v-for="(text, index) in texts" :key="index">
              <td>{{ text.id }}</td>
          <td><a href="#" :ref="text.id"  @click="onShowSentences(text)">
            {{ text.content }}</a></td>
              <td>
              </td>
            </tr>
           <tr v-if="rest"><td></td><td>
             <button type="button" class="btn btn-sm" @click="onNextPage()">
             Next</button></td></tr>
          </tbody>
        </table>
        <div ref="showSentences">Sentences
        <ul>
          <li v-for="(sent, index) in sents" :key="index" >
            <a href="#" :ref="textId+index" @click="onSimilarSentences(textId, index)">
            {{index + 1}}.{{sent}}</a>
            <div class="alert alert-success" >
              <ul>
                <li v-for="(ssent, index) in simsents[index]" :key="index" >{{ssent}}</li>
              </ul>
            </div>
        </li>
        </ul>
        </div>
      </div>
    </div>
    <b-modal ref="addTextModal"
            id="text-modal"
            title="Add a new text"
            hide-footer>
      <b-form @submit="onSubmit" @reset="onReset" class="w-100">
        <b-form-group id="form-content-group"
                    label="Content:"
                    label-for="form-content-input">
          <b-form-textarea id="form-content-input"
                        v-model="addTextForm.content"
                        required
                        placeholder="Enter text">
          </b-form-textarea>
        </b-form-group>
        <b-button-group>
          <b-button type="submit" variant="primary">Submit</b-button>
          <b-button type="reset" variant="danger">Reset</b-button>
        </b-button-group>
      </b-form>
    </b-modal>
  </div>
</template>

<script>
import axios from 'axios';
import Alert from './Alert.vue';

export default {
  data() {
    return {
      texts: [],
      addTextForm: {
        content: '',
      },
      message: '',
      showMessage: false,
      showSentences: false,
      textId: '',
      sents: [],
      simsents: {},
      currentPage: 0,
      rest: 0,
    };
  },
  components: {
    alert: Alert,
  },
  methods: {
    getTexts(page) {
      const path = `http://localhost:8888/api?q=texts&p=${page}`;
      axios.get(path)
        .then((res) => {
          this.texts = res.data.texts;
          this.currentPage = page;
          this.rest = res.data.rest;
        })
        .catch((error) => {
          // eslint-disable-next-line
          console.error(error);
        });
    },
    getSents(textId) {
      const path = `http://localhost:8888/api?q=sents&idt=${textId}&sn=0`;
      axios.get(path)
        .then((res) => {
          this.sents = res.data.texts;
          this.showSentences = true;
        })
        .catch((error) => {
          // eslint-disable-next-line
          console.error(error);
        });
    },
    addText(payload) {
      const path = 'http://localhost:8888/api';
      axios.post(path, payload)
        .then(() => {
          this.currentPage = 0;
          this.getTexts(this.currentPage);
          this.message = 'Text added!';
          this.showMessage = true;
        })
        .catch((error) => {
          // eslint-disable-next-line
          console.log(error);
          this.getTexts(this.currentPage);
        });
    },
    onNextPage() {
      this.getTexts(this.currentPage + 1);
    },
    onPreviousPage() {
      if (this.currentPage > 0) {
        this.getTexts(this.currentPage - 1);
      }
    },
    onShowSentences(text) {
      this.textId = text.id;
      this.getSents(text.id);
      this.showMessage = false;
      this.simsents = {};
      this.$refs.showSentences.scrollIntoView();
    },
    onSimilarSentences(textID, sn) {
      const path = `http://localhost:8888/api?q=simsents&idt=${textID}&sn=${sn}`;
      axios.get(path)
        .then((res) => {
          if (this.simsents[sn] === undefined) {
            this.simsents[sn] = res.data.texts;
          } else {
            delete this.simsents[sn];
          }
          this.$forceUpdate();
          this.$refs[textID + sn][0].scrollIntoView();
          console.log(textID, sn, this.simsents);
        })
        .catch((error) => {
          // eslint-disable-next-line
          console.error(error);
        });
    },
    initForm() {
      this.addTextForm.content = '';
    },
    onSubmit(evt) {
      evt.preventDefault();
      this.showMessage = false;
      this.simsents = {};
      this.$refs.addTextModal.hide();
      const payload = {
        q: 'add',
        content: this.addTextForm.content,
      };
      this.addText(payload);
      this.initForm();
    },
    onReset(evt) {
      evt.preventDefault();
      this.$refs.addTextModal.hide();
      this.initForm();
    },
  },
  created() {
    this.getTexts(this.currentPage);
  },
};
</script>
