// A $( document ).ready() block.
$(document).ready(function () {
    /**add add_user click listener*/
    $("#add_user").on("submit", add_user);
    /**add add_transaction click listener*/
    $("#add_transaction").on("submit", add_transaction);
    /**AJAX call to get selected (all) user(s)*/
    get_users();

    function get_users() {
        $.get({
            url: "user",
            dataType: "json"
        }).done(function (users) {
            update_userlist(users);
            add_user_click_handlers();
        }).fail(function(err) {
            alert(err);
        });
    }

    function update_userlist(users) {
        var source = $('#add_transaction_source');
        var target = $('#add_transaction_target');

        /**remove old user list*/
        $.each($("#users").find("li"), function(index, user) {
            user.remove();
        });

        /**remove add transaction select options*/
        $.each(source.find('option'), function (index, option) {
            $(option).remove();
        });
        $.each(target.find('option'), function (index, option) {
            $(option).remove();
        });

        /**fill list of users with response*/
        $.each(users, function (index, user) {
            var li_user =
                "<li class='user'>" +
                "<h5><a href='#" + user.id + "' class='user'>" + user.name + "</a></h5>" +
                "<h6>" + user.email + "</h6>" +
                "<h6>" + user.description + "</h6>" +
                "<h6>max per transaction: <strong>" + user.max_per_transaction + "</strong></h6>";
            if (user.account_bitcoin !== null) {
                li_user += "<h6>BTC Addr: <strong>" + user.account_bitcoin.id + "</strong></h6>" +
                    "<h6>BTC balance: <strong>" + user.account_bitcoin.balance + "</strong></h6>";
            }
            if (user.account_ethereum !== null) {
                li_user += "<h6>ETH Addr: <strong>" + user.account_ethereum.id + "</strong></h6>" +
                    "<h6>ETH balance: <strong>" + user.account_ethereum.balance + "</strong></h6>";
            }
            li_user += "</li>";
            $('#users').append(li_user);

            /**also fill options of transaction select fields*/
            var transaction_options = "<option value='" + user.id + "'>" + user.id + "</option>";
            source.append(transaction_options);
            target.append(transaction_options);
        });
    }

    function add_user_click_handlers() {
        $("#users").find("a").click(function (event) {
            event.preventDefault();
            var elem = $(this);
            var user_id = elem.attr('href').split('#')[1];
            $(elem).on('click', get_transactions_of(user_id));
        });
    }

    function get_transactions_of(user_id) {
        $.get({
            url: "history",
            data: {
                user_id: user_id
            },
            dataType: "json"
        }).done(function (json) {
            var transactions = $('#transactions');
            /**clean up old transactions*/
            $.each(transactions.find('li'), function (index, transaction) {
                transaction.remove();
            });
            /**add transactions of selected user*/
            $.each(json, function (index, transaction) {
                var li_transaction = "<li>" +
                    "<h5>id: <strong>" + transaction.id + "</strong></h5>" +
                    "<h6>currency: <strong>" + transaction.currency_type + "</strong></h6>" +
                    "<h6>amount: <strong>" + transaction.currency_amount + "</strong></h6>" +
                    "<h6>source: <strong>" + transaction.source_user_id + "</strong></h6>" +
                    "<h6>target: <strong>" + transaction.target_user_id + "</strong></h6>" +
                    "<h6>created: <strong>" + transaction.timestamp_created + "</strong></h6>" +
                    "<h6>processed: <strong>" + transaction.timestamp_processed + "</strong></h6>" +
                    "<h6>state: <strong>" + transaction.state + "</strong></h6>" +
                    "</li>";
                transactions.append(li_transaction);
            });
        }).fail(function(err) {
            alert(err);
        });
    }

    function add_user(event) {
        event.preventDefault();
        event.stopPropagation();

        var form = event.currentTarget;
        var data = {
            name: form[0].value,
            description: form[1].value,
            email: form[2].value,
            max_per_transaction: form[3].value,
            account_bitcoin: form[4].value,
            account_ethereum: form[5].value
        };
        $.post({
            url: "user",
            data: data,
            dataType: "json"
        }).done(function(json) {
            get_users();
        }).fail(function(err) {
            alert(err);
        });
    }

     function add_transaction(event) {
        event.preventDefault();
        event.stopPropagation();

        var form = event.currentTarget;
        var data = {
            source: form[0].value,
            target: form[1].value,
            currency: form[2].value,
            amount: form[3].value
        };
        $.post({
            url: "submit",
            data: data,
            dataType: "json"
        }).done(function(json) {
            get_transactions_of(json.source_user_id);
            get_users();
        }).fail(function(err) {
            alert(err);
        });
    }
});