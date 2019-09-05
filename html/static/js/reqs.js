var app = new Vue({
  el: '#app',
  methods: {
    get_jobs: function() {
            axios
                .get('http://127.0.0.1:5555/catalogue')
                .then(response => {
                            this.items = response.data['items'], console.log(response.data)})
  }
  },

  data:{
    items:[

    ]
  },

  created: function () {
    this.get_jobs()
  }

  })
